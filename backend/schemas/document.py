"""
Document Pydantic Schemas

Request/response models for document endpoints.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    """Schema for document data in responses."""
    id: int
    filename: str
    original_filename: str
    file_type: str
    file_size: int
    chunk_count: int
    status: str
    error_message: Optional[str] = None
    uploaded_at: datetime

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Schema for list of documents response."""
    documents: list[DocumentResponse]
    total: int
