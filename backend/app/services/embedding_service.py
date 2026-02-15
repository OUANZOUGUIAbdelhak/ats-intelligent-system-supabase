"""
Embedding service - sentence-transformers all-MiniLM-L6-v2 (384 dimensions).
"""

import logging
from typing import List

from app.core.config import settings

logger = logging.getLogger(__name__)

_model = None


def _get_model():
    """Lazy-load SentenceTransformer."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
            _model = SentenceTransformer(settings.EMBEDDING_MODEL)
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
    return _model


async def generate_embedding(text: str) -> List[float]:
    """Generate 384-dim embedding for text."""
    model = _get_model()
    if not model or not text:
        return [0.0] * settings.EMBEDDING_DIMENSION

    try:
        embedding = model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        return [0.0] * settings.EMBEDDING_DIMENSION
