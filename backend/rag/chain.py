"""
RAG Chain

Composes the full LCEL RAG pipeline:
    User Query → Retriever → Context Formatter → Prompt → LLM → Response Parser

Provides both streaming (SSE) and non-streaming execution modes.
"""

import json
from typing import AsyncGenerator

from backend.rag.retriever import retrieve, RetrievedChunk
from backend.rag.context_formatter import format_context
from backend.rag.prompts import get_rag_prompt
from backend.rag.llm_provider import get_llm
from backend.rag.response_parser import parse_response, ParsedResponse, SourceCitation
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def run_query(
    query: str,
    user_id: str,
    temperature: float | None = None,
    max_tokens: int | None = None,
    k: int = 4
) -> ParsedResponse:
    """
    Execute the full RAG pipeline (non-streaming).

    Pipeline: Retrieve → Format Context → Prompt → LLM → Parse Response

    Args:
        query: The user's question.
        user_id: The user's ID for document filtering.
        temperature: Optional LLM temperature override.
        max_tokens: Optional max tokens override.
        k: Number of chunks to retrieve.

    Returns:
        ParsedResponse with answer and source citations.
    """
    logger.info(f"Running RAG query for user {user_id}: {query[:100]}...")

    # Step 1: Retrieve relevant chunks
    chunks = retrieve(query, user_id, k)

    # Step 2: Format context
    context = format_context(chunks)

    # Step 3: Build prompt
    prompt = get_rag_prompt()
    messages = prompt.format_messages(context=context, question=query)

    # Step 4: Call LLM (non-streaming)
    llm = get_llm(temperature=temperature, max_tokens=max_tokens, streaming=False)
    response = llm.invoke(messages)

    # Step 5: Parse response
    result = parse_response(response.content, chunks)

    logger.info(f"RAG query complete: {len(result.sources)} sources cited")
    return result


async def stream_query(
    query: str,
    user_id: str,
    temperature: float | None = None,
    max_tokens: int | None = None,
    k: int = 4
) -> AsyncGenerator[str, None]:
    """
    Execute the RAG pipeline with streaming token output (SSE format).

    Yields Server-Sent Event formatted strings:
    - Token events: data: {"type": "token", "content": "..."}
    - Done event:   data: {"type": "done", "sources": [...], "conversation_id": N}
    - Error events:  data: {"type": "error", "content": "..."}

    Args:
        query: The user's question.
        user_id: The user's ID for document filtering.
        temperature: Optional LLM temperature override.
        max_tokens: Optional max tokens override.
        k: Number of chunks to retrieve.

    Yields:
        SSE-formatted event strings.
    """
    logger.info(f"Streaming RAG query for user {user_id}: {query[:100]}...")

    try:
        # Step 1: Retrieve relevant chunks
        chunks = retrieve(query, user_id, k)

        if not chunks:
            token_data = json.dumps({'type': 'token', 'content': "I don't have any uploaded documents to search. Please upload documents first."})
            done_data = json.dumps({'type': 'done', 'sources': []})
            yield f"data: {token_data}\n\n"
            yield f"data: {done_data}\n\n"
            return

        # Step 2: Format context
        context = format_context(chunks)

        # Step 3: Build prompt
        prompt = get_rag_prompt()
        messages = prompt.format_messages(context=context, question=query)

        # Step 4: Stream from LLM
        llm = get_llm(temperature=temperature, max_tokens=max_tokens, streaming=True)
        full_response = ""

        async for chunk in llm.astream(messages):
            token = chunk.content
            if token:
                full_response += token
                event = json.dumps({"type": "token", "content": token})
                yield f"data: {event}\n\n"

        # Step 5: Parse complete response for sources
        parsed = parse_response(full_response, chunks)

        # Build source citations for the done event
        sources_data = [
            {
                "document_name": s.document_name,
                "page_number": s.page_number,
                "text_snippet": s.text_snippet,
                "relevance_score": s.relevance_score,
            }
            for s in parsed.sources
        ]

        done_event = json.dumps({
            "type": "done",
            "sources": sources_data,
            "full_response": full_response,
        })
        yield f"data: {done_event}\n\n"

        logger.info(f"Streaming complete: {len(parsed.sources)} sources")

    except Exception as e:
        logger.error(f"Streaming RAG error: {e}")
        error_event = json.dumps({"type": "error", "content": str(e)})
        yield f"data: {error_event}\n\n"
