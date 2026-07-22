"""
Chat API Routes

Handles chat queries (streaming and non-streaming), conversation history,
and history management.
"""

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.database import get_db
from backend.models.user import User
from backend.models.chat import Conversation, Message
from backend.schemas.chat import (
    ChatRequest, ChatResponse, SourceCitation,
    ConversationResponse, ConversationDetailResponse,
    MessageResponse, HistoryResponse
)
from backend.auth.dependencies import get_current_user
from backend.rag.chain import run_query, stream_query
from backend.rag.analytics_engine import run_analytics_query
from backend.models.document import Document
from backend.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api", tags=["Chat"])


@router.post("/chat")
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a query to the RAG pipeline.

    If stream=True (default), returns a Server-Sent Events stream.
    If stream=False, returns a complete JSON response.

    Args:
        request: Chat request with query, optional conversation_id, settings.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        StreamingResponse (SSE) or ChatResponse (JSON).
    """
    user_id = str(current_user.id)

    # Get or create conversation
    if request.conversation_id:
        conversation = db.query(Conversation).filter(
            Conversation.id == request.conversation_id,
            Conversation.user_id == current_user.id
        ).first()
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
    else:
        # Create new conversation with title from query
        title = request.query[:80].strip()
        if len(request.query) > 80:
            title += "..."
        conversation = Conversation(
            user_id=current_user.id,
            title=title,
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    # Save user message
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=request.query,
    )
    db.add(user_message)
    db.commit()

    # Check for latest dataset to route to analytics engine
    dataset_doc = db.query(Document).filter(
        Document.user_id == current_user.id,
        Document.file_type.in_(["csv", "xlsx"])
    ).order_by(Document.uploaded_at.desc()).first()

    analytics_response = None
    if dataset_doc:
        analytics_response = run_analytics_query(dataset_doc.file_path, request.query)

    if analytics_response:
        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=analytics_response,
        )
        db.add(assistant_message)
        conversation.updated_at = datetime.now(timezone.utc)
        db.commit()
        
        if request.stream:
            async def event_generator():
                # Yield token event first so frontend stream accumulator receives content
                token_data = {
                    "type": "token",
                    "content": analytics_response
                }
                yield f"data: {json.dumps(token_data)}\n\n"

                data = {
                    "type": "done",
                    "full_response": analytics_response,
                    "sources": [],
                    "conversation_id": conversation.id
                }
                yield f"data: {json.dumps(data)}\n\n"
            return StreamingResponse(
                event_generator(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                }
            )
        else:
            return ChatResponse(
                answer=analytics_response,
                sources=[],
                conversation_id=conversation.id,
            )

    if request.stream:
        # Streaming response via SSE
        async def event_generator():
            full_response = ""
            sources_data = []

            async for event in stream_query(
                query=request.query,
                user_id=user_id,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            ):
                # Parse the event to capture the full response
                if event.startswith("data: "):
                    try:
                        data = json.loads(event[6:].strip())
                        if data.get("type") == "done":
                            full_response = data.get("full_response", full_response)
                            sources_data = data.get("sources", [])
                            # Add conversation_id to done event
                            data["conversation_id"] = conversation.id
                            event = f"data: {json.dumps(data)}\n\n"
                    except json.JSONDecodeError:
                        pass

                yield event

            # Save assistant message after streaming completes
            assistant_message = Message(
                conversation_id=conversation.id,
                role="assistant",
                content=full_response,
            )
            assistant_message.sources = sources_data
            db.add(assistant_message)

            # Update conversation timestamp
            conversation.updated_at = datetime.now(timezone.utc)
            db.commit()

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            }
        )

    else:
        # Non-streaming response
        result = run_query(
            query=request.query,
            user_id=user_id,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )

        # Save assistant message
        sources_list = [
            {
                "document_name": s.document_name,
                "page_number": s.page_number,
                "text_snippet": s.text_snippet,
                "relevance_score": s.relevance_score,
            }
            for s in result.sources
        ]

        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=result.answer,
        )
        assistant_message.sources = sources_list
        db.add(assistant_message)

        # Update conversation timestamp
        conversation.updated_at = datetime.now(timezone.utc)
        db.commit()

        return ChatResponse(
            answer=result.answer,
            sources=[
                SourceCitation(
                    document_name=s.document_name,
                    page_number=s.page_number,
                    text_snippet=s.text_snippet,
                    relevance_score=s.relevance_score,
                )
                for s in result.sources
            ],
            conversation_id=conversation.id,
        )


@router.get("/history", response_model=HistoryResponse)
async def get_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all conversations for the current user.

    Returns:
        List of conversation summaries with message counts.
    """
    conversations = (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )

    result = []
    for conv in conversations:
        msg_count = db.query(func.count(Message.id)).filter(
            Message.conversation_id == conv.id
        ).scalar()

        result.append(ConversationResponse(
            id=conv.id,
            title=conv.title,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            message_count=msg_count or 0,
        ))

    return HistoryResponse(conversations=result)


@router.get("/history/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all messages for a specific conversation.

    Args:
        conversation_id: ID of the conversation.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        Conversation with all messages and their source citations.

    Raises:
        HTTPException 404: If conversation not found or doesn't belong to user.
    """
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
        .all()
    )

    message_responses = []
    for msg in messages:
        sources = None
        if msg.sources:
            sources = [
                SourceCitation(**s) for s in msg.sources
            ]
        message_responses.append(MessageResponse(
            id=msg.id,
            role=msg.role,
            content=msg.content,
            sources=sources,
            created_at=msg.created_at,
        ))

    return ConversationDetailResponse(
        id=conversation.id,
        title=conversation.title,
        messages=message_responses,
        created_at=conversation.created_at,
    )


@router.delete("/history", status_code=status.HTTP_200_OK)
async def clear_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete all conversations and messages for the current user.

    Returns:
        Confirmation message with count of deleted conversations.
    """
    conversations = db.query(Conversation).filter(
        Conversation.user_id == current_user.id
    ).all()

    count = len(conversations)
    for conv in conversations:
        db.delete(conv)

    db.commit()

    logger.info(f"Cleared {count} conversations for user {current_user.id}")
    return {"message": f"Deleted {count} conversation(s)"}


@router.delete("/history/{conversation_id}", status_code=status.HTTP_200_OK)
async def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a specific conversation and its messages.

    Args:
        conversation_id: ID of the conversation to delete.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        Confirmation message.

    Raises:
        HTTPException 404: If conversation not found.
    """
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    db.delete(conversation)
    db.commit()

    logger.info(f"Deleted conversation {conversation_id} for user {current_user.id}")
    return {"message": "Conversation deleted successfully"}
