"""
Chunking Strategies

Text chunking implementations using the Strategy Pattern.
Currently implements RecursiveCharacterTextSplitter.
Designed so SemanticChunker can be added later without
changing any other module.
"""

from abc import ABC, abstractmethod

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from backend.rag.extractors import PageContent
from backend.config import get_settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class ChunkingStrategy(ABC):
    """Abstract base class for text chunking strategies."""

    @abstractmethod
    def chunk(
        self,
        pages: list[PageContent],
        metadata: dict
    ) -> list[Document]:
        """
        Split pages into chunks with metadata.

        Args:
            pages: List of extracted page contents.
            metadata: Base metadata to attach to each chunk
                      (e.g., user_id, document_id, source).

        Returns:
            List of LangChain Document objects with text and metadata.
        """
        pass


class RecursiveChunker(ChunkingStrategy):
    """
    Chunks text using LangChain's RecursiveCharacterTextSplitter.

    This is the default strategy (V1). It splits text by character
    boundaries with configurable chunk size and overlap.
    """

    def __init__(
        self,
        chunk_size: int = settings.CHUNK_SIZE,
        chunk_overlap: int = settings.CHUNK_OVERLAP
    ):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

    def chunk(
        self,
        pages: list[PageContent],
        metadata: dict
    ) -> list[Document]:
        """Split pages into overlapping chunks, preserving page numbers."""
        all_chunks = []

        for page in pages:
            # Split the page text
            texts = self.splitter.split_text(page.text)

            for text in texts:
                chunk_metadata = {
                    **metadata,
                    "page": page.page_number,
                    "source": page.source_file,
                }
                all_chunks.append(Document(
                    page_content=text,
                    metadata=chunk_metadata
                ))

        logger.info(
            f"Chunked {len(pages)} pages into {len(all_chunks)} chunks "
            f"(size={self.splitter._chunk_size}, overlap={self.splitter._chunk_overlap})"
        )
        return all_chunks


# --- Future: Semantic Chunker ---
# class SemanticChunker(ChunkingStrategy):
#     """
#     Chunks text using semantic similarity boundaries.
#     Uses langchain_experimental.text_splitter.SemanticChunker.
#     Drop-in replacement — no changes needed in document_processor.py.
#     """
#     def __init__(self, embeddings):
#         from langchain_experimental.text_splitter import SemanticChunker as LCSemanticChunker
#         self.splitter = LCSemanticChunker(embeddings)
#
#     def chunk(self, pages, metadata):
#         ...


# --- Factory ---

_STRATEGIES = {
    "recursive": RecursiveChunker,
    # "semantic": SemanticChunker,  # Add when ready
}


def get_chunking_strategy(
    strategy_name: str = "recursive",
    **kwargs
) -> ChunkingStrategy:
    """
    Get a chunking strategy by name.

    Args:
        strategy_name: Name of the strategy ('recursive', future: 'semantic').
        **kwargs: Additional arguments passed to the strategy constructor.

    Returns:
        An instance of the requested ChunkingStrategy.

    Raises:
        ValueError: If strategy name is not recognized.
    """
    if strategy_name not in _STRATEGIES:
        raise ValueError(
            f"Unknown chunking strategy: {strategy_name}. "
            f"Available: {list(_STRATEGIES.keys())}"
        )
    return _STRATEGIES[strategy_name](**kwargs)
