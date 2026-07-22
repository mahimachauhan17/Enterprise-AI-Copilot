"""
Qdrant Vector Store

Manages vector storage and retrieval using Qdrant with
persistent local storage. Provides methods to add, delete,
and search documents with relevance scores.
"""

from typing import Optional

from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http import models

from backend.rag.embeddings import get_embeddings
from backend.config import get_settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Singleton instance
_vector_store: Optional[QdrantVectorStore] = None

COLLECTION_NAME = "enterprise_copilot_docs"


def get_vector_store() -> QdrantVectorStore:
    """
    Get the shared Qdrant vector store instance.

    Returns:
        Initialized Qdrant vector store with persistence.
    """
    global _vector_store

    if _vector_store is None:
        logger.info(f"Initializing Qdrant at: {settings.VECTOR_STORE_DIR}")
        client = QdrantClient(path=settings.VECTOR_STORE_DIR)
        
        # Ensure collection exists
        if not client.collection_exists(COLLECTION_NAME):
            logger.info(f"Creating Qdrant collection: {COLLECTION_NAME}")
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=models.VectorParams(size=768, distance=models.Distance.COSINE),
            )
        
        _vector_store = QdrantVectorStore(
            client=client,
            collection_name=COLLECTION_NAME,
            embedding=get_embeddings(),
        )
        logger.info("Qdrant initialized successfully")

    return _vector_store


def add_documents(chunks: list[Document]) -> None:
    """
    Add document chunks to the vector store.

    Args:
        chunks: List of LangChain Document objects with text and metadata.
    """
    if not chunks:
        logger.warning("No chunks to add to vector store")
        return

    store = get_vector_store()
    store.add_documents(chunks)
    logger.info(f"Added {len(chunks)} chunks to vector store")


def delete_documents(document_id: str) -> None:
    """
    Delete all vectors associated with a document.

    Args:
        document_id: The document ID to remove (stored in metadata).
    """
    store = get_vector_store()

    try:
        # Delete by metadata filter
        store.client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="metadata.document_id",
                            match=models.MatchValue(value=document_id),
                        )
                    ]
                )
            ),
        )
        logger.info(f"Deleted vectors for document_id: {document_id}")
    except Exception as e:
        logger.error(f"Error deleting vectors for document_id {document_id}: {e}")
        raise


def similarity_search_with_scores(
    query: str,
    user_id: str,
    k: int = settings.RETRIEVER_K
) -> list[tuple[Document, float]]:
    """
    Search for similar documents with relevance scores.

    Args:
        query: The search query text.
        user_id: Filter results to this user's documents.
        k: Number of results to return.

    Returns:
        List of (Document, score) tuples, sorted by relevance.
        Higher scores indicate higher relevance in Qdrant (cosine similarity).
    """
    store = get_vector_store()

    try:
        qdrant_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="metadata.user_id",
                    match=models.MatchValue(value=user_id),
                )
            ]
        )
        
        results = store.similarity_search_with_score(
            query,
            k=k,
            filter=qdrant_filter
        )
        logger.debug(f"Found {len(results)} results for query (user: {user_id})")
        return results
    except Exception as e:
        logger.error(f"Vector search error: {e}")
        return []
