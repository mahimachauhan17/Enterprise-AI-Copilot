"""
Chat Pydantic Schemas

Request/response models for chat endpoints including
source citations with relevance scores.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Schema for chat query request."""
    query: str = Field(..., min_length=1, max_length=5000)
    conversation_id: Optional[int] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=1.0)
    max_tokens: Optional[int] = Field(None, ge=100, le=8192)
    stream: bool = True


class SourceCitation(BaseModel):
    """Schema for a source citation in responses."""
    document_name: str
    page_number: Optional[int] = None
    text_snippet: str
    relevance_score: Optional[float] = None


class ChatResponse(BaseModel):
    """Schema for non-streaming chat response."""
    answer: str
    sources: list[SourceCitation]
    conversation_id: int


class MessageResponse(BaseModel):
    """Schema for a single message in history."""
    id: int
    role: str
    content: str
    sources: Optional[list[SourceCitation]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    """Schema for a conversation summary."""
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    class Config:
        from_attributes = True


class ConversationDetailResponse(BaseModel):
    """Schema for a conversation with all messages."""
    id: int
    title: str
    messages: list[MessageResponse]
    created_at: datetime


class HistoryResponse(BaseModel):
    """Schema for list of conversations."""
    conversations: list[ConversationResponse]
