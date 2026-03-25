import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from routes.resume_routes import router
from routes.batch_routes import batch_router          # add this import

# ── Logging Setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


# ── Lifespan: Pre-load models at startup ─────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Loading NLP models...")
    from services.nlp_service import nlp              # spaCy
    from services.semantic_service import model        # sentence-transformers
    logger.info("Models loaded. Server ready.")
    yield
    logger.info("Shutting down.")

# ── App Init ──────────────────────────────────────────────────────────────────
app = FastAPI(
    title="ATS Resume Analyzer",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router, prefix="/api/v1")
app.include_router(batch_router, prefix="/api/v1")    



# ── Entry Point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # ✅ reload=True crashes on Windows (signal thread issue)
    )
    