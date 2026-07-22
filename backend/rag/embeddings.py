"""
HuggingFace Embeddings

Singleton wrapper for the HuggingFace embedding model.
The model is loaded once and shared across the application
to avoid reloading the ~440MB model repeatedly.

Change the model by setting EMBEDDING_MODEL in .env.
"""

from typing import Optional

from langchain_huggingface import HuggingFaceEmbeddings

from backend.config import get_settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Singleton instance
_embeddings_instance: Optional[HuggingFaceEmbeddings] = None


def get_embeddings() -> HuggingFaceEmbeddings:
    """
    Get the shared HuggingFace embeddings instance.

    On first call, downloads and loads the model (may take a moment).
    Subsequent calls return the cached instance.

    Returns:
        HuggingFaceEmbeddings instance ready for use.
    """
    global _embeddings_instance

    if _embeddings_instance is None:
        logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
        _embeddings_instance = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True}
        )
        logger.info("Embedding model loaded successfully")

    return _embeddings_instance
