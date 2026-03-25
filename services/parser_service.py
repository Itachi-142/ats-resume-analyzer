# ✅ FIXED — parser_service.py

import io
import logging
import fitz                          # PyMuPDF
from docx import Document
from fastapi import UploadFile

logger = logging.getLogger(__name__)


# ── TXT ───────────────────────────────────────────────────────────────────────

async def _read_txt(file: UploadFile) -> str:
    content = await file.read()
    return content.decode("utf-8", errors="ignore")


# ── DOCX ──────────────────────────────────────────────────────────────────────

async def _read_docx(file: UploadFile) -> str:
    content = await file.read()

    # BytesIO eliminates the temp file entirely — no race conditions
    doc = Document(io.BytesIO(content))

    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)


# ── PDF ───────────────────────────────────────────────────────────────────────

async def _read_pdf(file: UploadFile) -> str:
    content = await file.read()

    # fitz.open() accepts raw bytes via stream — no temp file needed
    with fitz.open(stream=content, filetype="pdf") as doc:
        text = "\n".join(page.get_text() for page in doc)

    return text


# ── Main Dispatcher ───────────────────────────────────────────────────────────

async def extract_text(file: UploadFile) -> str:
    filename = file.filename.lower()

    try:
        if filename.endswith(".txt"):
            return await _read_txt(file)

        elif filename.endswith(".docx"):
            return await _read_docx(file)

        elif filename.endswith(".pdf"):
            return await _read_pdf(file)

        else:
            raise ValueError(f"Unsupported file type: '{filename}'")

    except ValueError:
        raise  # Let the route handle this as a 400

    except Exception as e:
        logger.error("Failed to parse file '%s': %s", file.filename, str(e), exc_info=True)
        raise RuntimeError(f"Could not read file '{file.filename}'. It may be corrupt or password-protected.")