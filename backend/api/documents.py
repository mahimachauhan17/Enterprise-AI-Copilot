"""
Document API Routes

Handles document upload, listing, searching, and deletion.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from backend.database import get_db
from backend.models.user import User
from backend.models.document import Document
from backend.schemas.document import DocumentResponse, DocumentListResponse
from backend.auth.dependencies import get_current_user
from backend.config import get_settings
from backend.utils.file_utils import validate_file_type, save_upload_file, get_file_extension, delete_file
from backend.rag.document_processor import process_document
from backend.rag.vector_store import delete_documents as delete_vectors
from backend.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api", tags=["Documents"])
settings = get_settings()


@router.post("/upload", response_model=list[DocumentResponse])
async def upload_documents(
    files: list[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload one or more documents for RAG processing.

    Supports PDF, DOCX, and TXT files. Each file is saved to disk,
    then processed through the RAG pipeline (extract → chunk → embed → store).

    Args:
        files: List of uploaded files.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        List of created document metadata records.

    Raises:
        HTTPException 400: If file type is not supported.
        HTTPException 413: If file exceeds size limit.
    """
    uploaded_docs = []

    for file in files:
        # Validate file type
        if not validate_file_type(file.filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file.filename}. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )

        # Save file to disk
        saved_name, file_path = await save_upload_file(file, settings.UPLOAD_DIR)
        file_ext = get_file_extension(file.filename)

        # Get file size
        import os
        file_size = os.path.getsize(file_path)

        # Check size limit
        if file_size > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
            delete_file(file_path)
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File {file.filename} exceeds {settings.MAX_UPLOAD_SIZE_MB}MB limit"
            )

        # Create database record
        doc = Document(
            user_id=current_user.id,
            filename=saved_name,
            original_filename=file.filename,
            file_type=file_ext.lstrip("."),
            file_size=file_size,
            file_path=file_path,
            status="processing",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        # Process document through RAG pipeline
        try:
            chunk_count = process_document(
                file_path=file_path,
                file_type=file_ext,
                document_id=doc.id,
                user_id=current_user.id,
                original_filename=file.filename,
                db=db,
            )
            db.refresh(doc)
            logger.info(f"Document processed: {file.filename} ({chunk_count} chunks)")
        except Exception as e:
            logger.error(f"Failed to process {file.filename}: {e}")
            db.refresh(doc)  # Refresh to get error status

        uploaded_docs.append(DocumentResponse.model_validate(doc))

    return uploaded_docs


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    search: Optional[str] = Query(None, description="Search documents by filename"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all documents uploaded by the current user.

    Args:
        search: Optional filename search query.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        List of document metadata records with total count.
    """
    query = db.query(Document).filter(Document.user_id == current_user.id)

    if search:
        query = query.filter(
            Document.original_filename.ilike(f"%{search}%")
        )

    documents = query.order_by(Document.uploaded_at.desc()).all()

    return DocumentListResponse(
        documents=[DocumentResponse.model_validate(d) for d in documents],
        total=len(documents)
    )


@router.delete("/document/{document_id}", status_code=status.HTTP_200_OK)
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a document and its vectors from the system.

    Removes the document from: database, disk, and ChromaDB.

    Args:
        document_id: ID of the document to delete.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        Confirmation message.

    Raises:
        HTTPException 404: If document not found or doesn't belong to user.
    """
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    # Delete vectors from ChromaDB
    try:
        delete_vectors(str(doc.id))
    except Exception as e:
        logger.error(f"Error deleting vectors for doc {doc.id}: {e}")

    # Delete file from disk
    delete_file(doc.file_path)

    # Delete from database
    db.delete(doc)
    db.commit()

    logger.info(f"Document deleted: {doc.original_filename} (id={doc.id})")

    return {"message": f"Document '{doc.original_filename}' deleted successfully"}
