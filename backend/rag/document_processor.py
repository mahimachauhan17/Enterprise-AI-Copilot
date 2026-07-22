"""
Document Processor

Orchestrates the full document processing pipeline:
Extract text → Chunk → Embed → Store in ChromaDB.

Updates document status in the database throughout processing.
"""

from sqlalchemy.orm import Session

from backend.rag.extractors import get_extractor
from backend.rag.chunking import get_chunking_strategy
from backend.rag.vector_store import add_documents
from backend.models.document import Document
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def process_document(
    file_path: str,
    file_type: str,
    document_id: int,
    user_id: int,
    original_filename: str,
    db: Session,
    chunking_strategy: str = "recursive"
) -> int:
    """
    Process an uploaded document through the full RAG ingestion pipeline.

    Pipeline: Extract → Chunk → Embed → Store

    Args:
        file_path: Path to the uploaded file on disk.
        file_type: File extension (e.g., '.pdf').
        document_id: Database ID of the Document record.
        user_id: ID of the user who uploaded the document.
        original_filename: Original filename for metadata.
        db: SQLAlchemy session for status updates.
        chunking_strategy: Name of the chunking strategy to use.

    Returns:
        Number of chunks created and stored.

    Raises:
        Exception: If any pipeline stage fails (status set to 'error').
    """
    doc_record = db.query(Document).filter(Document.id == document_id).first()

    try:
        # Stage 1: Extract text
        logger.info(f"[Doc {document_id}] Extracting text from {original_filename}")
        extractor = get_extractor(file_type)
        pages = extractor.extract(file_path)

        if not pages:
            raise ValueError(f"No text content extracted from {original_filename}")

        # Stage 2: Chunk text
        logger.info(f"[Doc {document_id}] Chunking {len(pages)} pages")
        chunker = get_chunking_strategy(chunking_strategy)
        metadata = {
            "user_id": str(user_id),
            "document_id": str(document_id),
            "original_filename": original_filename,
        }
        chunks = chunker.chunk(pages, metadata)

        if not chunks:
            raise ValueError(f"No chunks produced from {original_filename}")

        # Stage 3: Embed and store in ChromaDB
        logger.info(f"[Doc {document_id}] Storing {len(chunks)} chunks in vector store")
        add_documents(chunks)

        # Update document status
        if doc_record:
            doc_record.chunk_count = len(chunks)
            doc_record.status = "ready"
            db.commit()

        logger.info(
            f"[Doc {document_id}] Processing complete: "
            f"{len(chunks)} chunks from {original_filename}"
        )
        return len(chunks)

    except Exception as e:
        logger.error(f"[Doc {document_id}] Processing failed: {e}")
        if doc_record:
            doc_record.status = "error"
            doc_record.error_message = str(e)[:500]
            db.commit()
        raise
