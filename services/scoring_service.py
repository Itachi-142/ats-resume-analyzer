# services/scoring_service.py

import logging
from services.semantic_service import matcher
from services.skill_service    import (
    extract_skills,
    compute_tfidf_keyword_score,  # ← upgraded
    compute_keyword_score,         # ← kept for confidence calc
)
from services.feedback_service import generate_feedback
from models.schemas            import ScoreBreakdown, FeedbackDetail

logger = logging.getLogger(__name__)


def _compute_confidence(
    keyword_score:   float,
    semantic_score:  float,
    matched_count:   int,
    jd_skills_count: int,
) -> float:
    agreement   = 1.0 - abs(keyword_score - semantic_score)
    sufficiency = min(1.0, jd_skills_count / 10.0)
    coverage    = matched_count / max(jd_skills_count, 1)
    confidence  = (0.5 * agreement) + (0.3 * sufficiency) + (0.2 * coverage)
    return round(min(max(confidence, 0.0), 1.0), 3)


async def calculate_score(
    resume_text:     str,
    job_description: str,
) -> dict:

    # ── 1. Skill Extraction ───────────────────────────────────────────────────
    # Now returns jd_skills_set too — needed for TF-IDF weighting
    matched_skills, missing_skills, jd_skills_set = extract_skills(
        resume_text, job_description
    )
    jd_skills_count = len(jd_skills_set)

    # ── 2. TF-IDF Keyword Score ───────────────────────────────────────────────
    # Weights rare skills higher than common ones
    keyword_score = compute_tfidf_keyword_score(matched_skills, jd_skills_set)

    logger.info(
        "TF-IDF keyword score: %.3f | Matched: %d | JD skills: %d",
        keyword_score, len(matched_skills), jd_skills_count,
    )

    # ── 3. Semantic Score ─────────────────────────────────────────────────────
    semantic_score = await matcher.compute_semantic_score(
        resume_text, job_description
    )

    # ── 4. Weighted Final Score ───────────────────────────────────────────────
    final_score = round((0.4 * keyword_score) + (0.6 * semantic_score), 4)

    logger.info(
        "Scores — keyword(tfidf): %.3f | semantic: %.3f | final: %.3f",
        keyword_score, semantic_score, final_score,
    )

    # ── 5. Confidence ─────────────────────────────────────────────────────────
    confidence = _compute_confidence(
        keyword_score, semantic_score,
        len(matched_skills), jd_skills_count,
    )

    # ── 6. LLM Feedback ───────────────────────────────────────────────────────
    feedback: FeedbackDetail = await generate_feedback(
        resume_text     = resume_text,
        job_description = job_description,
        matched_skills  = matched_skills,
        missing_skills  = missing_skills,
        keyword_score   = keyword_score,
        semantic_score  = semantic_score,
        final_score     = final_score,
    )

    # ── 7. Return ─────────────────────────────────────────────────────────────
    return {
        "scores": ScoreBreakdown(
            keyword    = round(keyword_score,  3),
            semantic   = round(semantic_score, 3),
            final      = round(final_score,    3),
            confidence = confidence,
        ),
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "feedback":       feedback,
    }