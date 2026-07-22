"""
Context Formatter

Formats retrieved document chunks into a structured context
string with source markers for the LLM prompt.

Each source is numbered so the LLM can reference them in its response,
and the response_parser can map them back to source citations.
"""

from backend.rag.retriever import RetrievedChunk
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def format_context(chunks: list[RetrievedChunk]) -> str:
    """
    Format retrieved chunks into a structured context block.

    Each chunk is wrapped with a numbered source marker that includes
    the document name and page number. This allows the LLM to cite
    sources and the response_parser to extract citations.

    Args:
        chunks: List of retrieved chunks with metadata.

    Returns:
        Formatted context string ready for prompt injection.
        Returns a "no context" message if chunks is empty.

    Example output:
        [Source 1: company_policy.pdf, Page 3]
        All full-time employees are entitled to 24 days...

        [Source 2: handbook.docx, Page 1]
        The company observes 12 public holidays...
    """
    if not chunks:
        return "No relevant documents found. Please inform the user that no documents are available to answer their question."

    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        page_info = f", Page {chunk.page_number}" if chunk.page_number else ""
        header = f"[Source {i}: {chunk.document_name}{page_info}]"
        context_parts.append(f"{header}\n{chunk.content}")

    context = "\n\n".join(context_parts)
    logger.debug(f"Formatted context with {len(chunks)} sources ({len(context)} chars)")
    return context
