import logging
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from models.schemas import AnalyzeResponse

from services.parser_service import extract_text
from services.pre_processing import clean_text
from services.scoring_service import calculate_score

router = APIRouter()
logger = logging.getLogger(__name__)

MAX_FILE_SIZE_MB = 5

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_resume(
    file: UploadFile = File(...),
    job_description: str = Form(...),
):
    try:
        # 1. Validate file type
        if not file.filename.endswith((".txt", ".docx", ".pdf")):
            raise HTTPException(status_code=400, detail="Unsupported file type. Use PDF, DOCX, or TXT.")

        # 2. Validate file size
        contents = await file.read()
        size_mb = len(contents) / (1024 * 1024)
        if size_mb > MAX_FILE_SIZE_MB:
            raise HTTPException(
                status_code=400,
                detail=f"File too large ({size_mb:.1f}MB). Max allowed: {MAX_FILE_SIZE_MB}MB."
            )
        await file.seek(0)  # Reset pointer after reading

        # 3. Extract text
        resume_raw = await extract_text(file)
        if not resume_raw.strip():
            raise HTTPException(status_code=400, detail="Resume appears to be empty or unreadable.")

        logger.info("File '%s' parsed. Characters: %d", file.filename, len(resume_raw))

        # 4. Clean text
        resume_text = clean_text(resume_raw)
        job_text    = clean_text(job_description)

        # 5. ✅ Pass ONLY resume and JD — scoring service handles everything else
        result = await calculate_score(resume_text, job_text)

        # 6. Return validated response
        return AnalyzeResponse(**result)

    except HTTPException:
        raise

    except Exception as e:
        logger.error("Unhandled error in /analyze: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal analysis error. Please try again.")
    
    
    