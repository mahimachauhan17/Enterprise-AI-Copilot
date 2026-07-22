"""
Response Parser

Parses the LLM output and maps [Source N] references back
to the retrieved chunks to produce structured source citations
with document name, page number, text snippet, and relevance score.
"""

import re
from dataclasses import dataclass
from typing import Optional

from backend.rag.retriever import RetrievedChunk
from backend.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class SourceCitation:
    """A structured source citation for display."""
    document_name: str
    page_number: Optional[int]
    text_snippet: str
    relevance_score: Optional[float]


@dataclass
class ParsedResponse:
    """The parsed LLM response with answer and source citations."""
    answer: str
    sources: list[SourceCitation]


def parse_response(
    llm_output: str,
    retrieved_chunks: list[RetrievedChunk]
) -> ParsedResponse:
    """
    Parse the LLM output and extract source citations.

    Scans the LLM output for [Source N] references and maps them
    to the original retrieved chunks. Always includes all retrieved
    chunks as sources (even if not explicitly cited by the LLM)
    since they were used as context.

    Args:
        llm_output: The raw text output from the LLM.
        retrieved_chunks: The chunks that were used as context.

    Returns:
        ParsedResponse with the answer text and structured citations.
    """
    # Find all [Source N] references in the output
    cited_indices = set()
    pattern = r'\[Source\s+(\d+)\]'
    matches = re.findall(pattern, llm_output)
    for match in matches:
        cited_indices.add(int(match) - 1)  # Convert to 0-indexed

    # Build source citations from all retrieved chunks
    sources = []
    for i, chunk in enumerate(retrieved_chunks):
        # Truncate snippet for display
        snippet = chunk.content[:300].strip()
        if len(chunk.content) > 300:
            snippet += "..."

        citation = SourceCitation(
            document_name=chunk.document_name,
            page_number=chunk.page_number,
            text_snippet=snippet,
            relevance_score=chunk.relevance_score,
        )
        sources.append(citation)

    logger.debug(
        f"Parsed response: {len(sources)} sources, "
        f"{len(cited_indices)} explicitly cited"
    )

    return ParsedResponse(
        answer=llm_output,
        sources=sources
    )
