# routes/batch_routes.py
import logging
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List
from services.parser_service import extract_text
from services.pre_processing import clean_text
from services.scoring_service import calculate_score
from models.schemas import BatchAnalyzeResponse, CandidateResult

batch_router = APIRouter()
logger       = logging.getLogger(__name__)

@batch_router.post("/batch-analyze", response_model=BatchAnalyzeResponse)
async def batch_analyze_resumes(
    files: List[UploadFile] = File(...),
    job_description: str    = Form(...),
):
    if len(files) < 2:
        raise HTTPException(status_code=400, detail="Upload at least 2 resumes.")
    if len(files) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 resumes allowed.")

    job_text = clean_text(job_description)
    results  = []

    for file in files:
        if not file.filename.endswith((".pdf", ".docx", ".txt")):
            continue
        try:
            contents = await file.read()
            if len(contents) / (1024*1024) > 5:
                continue
            await file.seek(0)
            resume_raw = await extract_text(file)
            if not resume_raw.strip():
                continue
            resume_text = clean_text(resume_raw)
            result      = await calculate_score(resume_text, job_text)
            results.append(CandidateResult(
                rank=0, filename=file.filename,
                scores=result["scores"],
                matched_skills=result["matched_skills"],
                missing_skills=result["missing_skills"],
                feedback=result["feedback"],
            ))
            logger.info("Processed '%s' → %.3f", file.filename, result["scores"].final)
        except Exception as e:
            logger.error("Failed '%s': %s", file.filename, str(e))
            continue

    if not results:
        raise HTTPException(status_code=422, detail="No valid resumes could be processed.")

    results.sort(key=lambda x: x.scores.final, reverse=True)
    for i, c in enumerate(results):
        c.rank = i + 1

    return BatchAnalyzeResponse(
        total_candidates=len(results),
        job_description=job_description[:200],
        candidates=results,
    )