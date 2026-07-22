"""
Document SQLAlchemy Model

Stores metadata about uploaded documents.
"""

from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger
from sqlalchemy.orm import relationship

from backend.database import Base


class Document(Base):
    """Uploaded document metadata model."""

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=False)
    file_type = Column(String(10), nullable=False)  # pdf, docx, txt
    file_size = Column(BigInteger, nullable=False)  # bytes
    file_path = Column(String(1000), nullable=False)
    chunk_count = Column(Integer, default=0)
    status = Column(String(20), default="processing")  # processing, ready, error
    error_message = Column(String(1000), nullable=True)
    uploaded_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    owner = relationship("User", back_populates="documents")

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, filename={self.filename}, status={self.status})>"
