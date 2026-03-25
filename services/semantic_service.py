# services/semantic_service.py

import logging
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

MAX_CHARS = 8000  # Safe input limit

# ── Model ─────────────────────────────────────────────────────────────────────
# Loads once at startup via lifespan in main.py
# all-MiniLM-L6-v2 is fast, lightweight, and excellent for semantic similarity

try:
    model = SentenceTransformer("all-MiniLM-L6-v2")
    logger.info("SentenceTransformer loaded: all-MiniLM-L6-v2")
except Exception as e:
    raise RuntimeError(
        f"Failed to load SentenceTransformer: {e}\n"
        f"Run: pip install sentence-transformers"
    )


class SemanticMatcher:
    """
    Computes cosine similarity between resume and JD
    using sentence-transformers — fully local, no API needed.
    Cloud-ready.
    """

    @staticmethod
    def _cosine(a: np.ndarray, b: np.ndarray) -> float:
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            logger.warning("Zero vector in cosine similarity. Returning 0.0.")
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    async def compute_semantic_score(
        self,
        resume: str,
        jd:     str,
    ) -> float:
        """
        Compute semantic similarity score between resume and JD.
        Returns float between 0.0 and 1.0.
        """
        import asyncio

        try:
            # Run CPU-bound encoding in thread pool
            # Prevents blocking the FastAPI event loop
            resume_trunc = resume[:MAX_CHARS]
            jd_trunc     = jd[:MAX_CHARS]

            def _encode():
                embeddings = model.encode(
                    [resume_trunc, jd_trunc],
                    convert_to_numpy=True,
                    show_progress_bar=False,
                )
                return embeddings[0], embeddings[1]

            emb_resume, emb_jd = await asyncio.to_thread(_encode)

            score = self._cosine(emb_resume, emb_jd)
            score = max(0.0, min(1.0, score))

            logger.info("Semantic score: %.4f", score)
            return round(score, 4)

        except Exception as e:
            logger.error("Semantic scoring failed: %s", str(e), exc_info=True)
            return 0.0  # Safe fallback


# Global singleton
matcher = SemanticMatcher()