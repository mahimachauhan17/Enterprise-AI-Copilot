"""
Retriever Module

Queries the ChromaDB vector store and returns ranked chunks
with relevance scores. Filters by user_id so users only see
their own documents.

Designed as a callable component for the LCEL pipeline.
"""

from dataclasses import dataclass, field
from typing import Optional

from backend.rag.vector_store import similarity_search_with_scores
from backend.config import get_settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


@dataclass
class RetrievedChunk:
    """A retrieved document chunk with metadata and relevance score."""
    content: str
    document_name: str
    page_number: Optional[int] = None
    relevance_score: Optional[float] = None
    document_id: Optional[str] = None


def retrieve(
    query: str,
    user_id: str,
    k: int = settings.RETRIEVER_K
) -> list[RetrievedChunk]:
    """
    Retrieve relevant document chunks for a query.

    Args:
        query: The user's question.
        user_id: Filter results to this user's documents.
        k: Number of chunks to retrieve.

    Returns:
        List of RetrievedChunk objects sorted by relevance.
    """
    results = similarity_search_with_scores(query, user_id, k)

    chunks = []
    for doc, score in results:
        # Qdrant returns cosine similarity (higher is more relevant)
        relevance = max(0.0, min(1.0, score))

        chunk = RetrievedChunk(
            content=doc.page_content,
            document_name=doc.metadata.get("original_filename", doc.metadata.get("source", "Unknown")),
            page_number=doc.metadata.get("page"),
            relevance_score=round(relevance, 4),
            document_id=doc.metadata.get("document_id"),
        )
        chunks.append(chunk)

    logger.info(
        f"Retrieved {len(chunks)} chunks for query "
        f"(user: {user_id}, top_score: {chunks[0].relevance_score if chunks else 'N/A'})"
    )
    return chunks
