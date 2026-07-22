"""
User SQLAlchemy Model

Stores user account information for authentication.
"""

from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship

from backend.database import Base


class User(Base):
    """User account model."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    documents = relationship("Document", back_populates="owner", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="owner", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username})>"
