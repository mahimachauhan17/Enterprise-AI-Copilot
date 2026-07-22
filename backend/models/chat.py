"""
Chat SQLAlchemy Models

Stores conversations and messages for chat history.
"""

import json
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from backend.database import Base


class Conversation(Base):
    """Chat conversation model."""

    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(500), default="New Chat")
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    owner = relationship("User", back_populates="conversations")
    messages = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan",
        order_by="Message.created_at"
    )

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, title={self.title})>"


class Message(Base):
    """Chat message model."""

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(
        Integer, ForeignKey("conversations.id"), nullable=False, index=True
    )
    role = Column(String(20), nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    sources_json = Column(Text, nullable=True)  # JSON string of source citations
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

    @property
    def sources(self) -> list[dict] | None:
        """Deserialize sources from JSON."""
        if self.sources_json:
            return json.loads(self.sources_json)
        return None

    @sources.setter
    def sources(self, value: list[dict] | None) -> None:
        """Serialize sources to JSON."""
        if value:
            self.sources_json = json.dumps(value)
        else:
            self.sources_json = None

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, role={self.role})>"
