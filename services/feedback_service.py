# services/feedback_service.py

import logging
from groq import Groq
from dotenv import load_dotenv
import os
import json
import re

from models.schemas import FeedbackDetail, Recommendation

load_dotenv()

logger     = logging.getLogger(__name__)
MODEL_NAME = "llama-3.1-8b-instant"
client     = Groq(api_key=os.getenv("GROQ_API_KEY"))


# ── Prompt Builder ────────────────────────────────────────────────────────────

def _build_prompt(
    resume_text:     str,
    job_description: str,
    matched_skills:  list[str],
    missing_skills:  list[str],
    keyword_score:   float,
    semantic_score:  float,
    final_score:     float,
) -> str:
    matched_str = ", ".join(matched_skills) if matched_skills else "None identified"
    missing_str = ", ".join(missing_skills) if missing_skills else "None identified"

    return f"""You are a senior technical recruiter with 10+ years of hiring experience.

Evaluate this candidate strictly based on the data below. Do NOT invent skills or experience.

## Scores
- Keyword Match : {keyword_score:.0%}
- Semantic Match: {semantic_score:.0%}
- Overall Score : {final_score:.0%}

## Matched Skills
{matched_str}

## Missing Skills
{missing_str}

## Job Description (excerpt)
{job_description[:1500]}

## Resume (excerpt)
{resume_text[:2000]}

## Instructions
Respond ONLY with a valid JSON object. No markdown fences. No explanation outside JSON.

{{
  "summary": "2-3 sentence executive summary of candidate fit",
  "strengths": [
    "Specific strength with evidence from resume",
    "Specific strength with evidence from resume",
    "Specific strength with evidence from resume"
  ],
  "improvements": [
    "Specific actionable gap based only on missing skills",
    "Specific actionable gap based only on missing skills",
    "Specific actionable gap based only on missing skills"
  ],
  "recommendation": "Exactly one of: Strong Yes - Advance to Interview | Yes - Schedule Interview | Maybe - Interview with Reservations | No - Does Not Meet Requirements | Strong No - Significant Skills Gap"
}}

Rules:
- Reference actual skills from the lists above
- Never write generic advice like 'improve your resume'
- Strengths must cite specific matched skills
- Improvements must cite specific missing skills
- Recommendation must be word-for-word from the options above
"""


# ── JSON Parser ───────────────────────────────────────────────────────────────

def _parse_llm_response(raw: str, final_score: float) -> FeedbackDetail | None:

    # Try direct parse
    try:
        data = json.loads(raw.strip())
    except json.JSONDecodeError:
        # Try extracting JSON object from surrounding text
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            return None
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError:
            return None

    # Map recommendation to enum
    rec_raw = data.get("recommendation", "")
    try:
        recommendation = Recommendation(rec_raw)
    except ValueError:
        # Score-based fallback if LLM gave invalid value
        if final_score >= 0.75:
            recommendation = Recommendation.YES
        elif final_score >= 0.50:
            recommendation = Recommendation.MAYBE
        else:
            recommendation = Recommendation.NO
        logger.warning("Invalid recommendation '%s'. Mapped by score.", rec_raw)

    return FeedbackDetail(
        summary        = data.get("summary", "Evaluation complete."),
        strengths      = data.get("strengths", ["See matched skills above"]),
        improvements   = data.get("improvements", ["Address missing skills listed above"]),
        recommendation = recommendation,
    )


# ── Fallback ──────────────────────────────────────────────────────────────────

def _fallback_feedback(
    final_score:    float,
    matched_skills: list[str],
    missing_skills: list[str],
) -> FeedbackDetail:
    """Rule-based feedback when Groq is unavailable. Never returns None."""

    if final_score >= 0.75:
        rec     = Recommendation.YES
        summary = f"Strong candidate with {len(matched_skills)} matched skills."
    elif final_score >= 0.50:
        rec     = Recommendation.MAYBE
        summary = f"Partial match. {len(matched_skills)} skills aligned, {len(missing_skills)} gaps found."
    else:
        rec     = Recommendation.NO
        summary = f"Significant gap. {len(missing_skills)} required skills are missing."

    return FeedbackDetail(
        summary        = summary,
        strengths      = [f"Proficiency in {s}" for s in matched_skills[:3]] or ["Review resume manually"],
        improvements   = [f"Develop skills in: {s}" for s in missing_skills[:3]] or ["Align with JD requirements"],
        recommendation = rec,
    )


# ── Public Interface ──────────────────────────────────────────────────────────

async def generate_feedback(
    resume_text:     str,
    job_description: str,
    matched_skills:  list[str],
    missing_skills:  list[str],
    keyword_score:   float,
    semantic_score:  float,
    final_score:     float,
) -> FeedbackDetail:
    """
    Generates structured recruiter-style feedback using Groq API.
    Groq is synchronous but extremely fast (~1-2 seconds).
    Runs in thread pool to avoid blocking the event loop.
    """
    import asyncio

    prompt = _build_prompt(
        resume_text, job_description,
        matched_skills, missing_skills,
        keyword_score, semantic_score, final_score,
    )

    def _call_groq() -> str:
        response = client.chat.completions.create(
            model       = MODEL_NAME,
            messages    = [{"role": "user", "content": prompt}],
            temperature = 0.3,
            max_tokens  = 1024,
        )
        return response.choices[0].message.content.strip()

    try:
        # Run synchronous Groq call in thread pool
        raw = await asyncio.wait_for(
            asyncio.to_thread(_call_groq),
            timeout=30.0,
        )

        logger.debug("Groq raw response (first 300): %s", raw[:300])

        parsed = _parse_llm_response(raw, final_score)

        if parsed:
            logger.info("Groq feedback generated successfully.")
            return parsed

        logger.warning("Groq response could not be parsed. Using fallback.")
        return _fallback_feedback(final_score, matched_skills, missing_skills)

    except asyncio.TimeoutError:
        logger.error("Groq timed out after 30s. Using fallback.")
        return _fallback_feedback(final_score, matched_skills, missing_skills)

    except Exception as e:
        logger.error("Groq call failed: %s", str(e), exc_info=True)
        return _fallback_feedback(final_score, matched_skills, missing_skills)
