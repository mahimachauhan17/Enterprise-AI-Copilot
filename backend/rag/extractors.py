"""
Text Extractors

Extracts text content from PDF, DOCX, and TXT files.
Uses PyMuPDF (fitz) for accurate PDF text extraction.

Implements a factory pattern so new extractors can be added
without modifying existing code.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

import fitz  # PyMuPDF
from docx import Document as DocxDocument

from backend.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PageContent:
    """Represents extracted text from a single page/section."""
    text: str
    page_number: int
    source_file: str


class TextExtractor(ABC):
    """Abstract base class for text extractors."""

    @abstractmethod
    def extract(self, file_path: str) -> list[PageContent]:
        """
        Extract text content from a file.

        Args:
            file_path: Path to the file.

        Returns:
            List of PageContent objects, one per page/section.
        """
        pass


class PDFExtractor(TextExtractor):
    """Extracts text from PDF files using PyMuPDF (fitz)."""

    def extract(self, file_path: str) -> list[PageContent]:
        """Extract text from each page of a PDF."""
        pages = []
        filename = Path(file_path).name

        try:
            doc = fitz.open(file_path)
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text("text").strip()
                if text:
                    pages.append(PageContent(
                        text=text,
                        page_number=page_num + 1,  # 1-indexed
                        source_file=filename
                    ))
            doc.close()
            logger.info(f"Extracted {len(pages)} pages from PDF: {filename}")
        except Exception as e:
            logger.error(f"Error extracting PDF {filename}: {e}")
            raise

        return pages


class DOCXExtractor(TextExtractor):
    """Extracts text from DOCX files using python-docx."""

    def extract(self, file_path: str) -> list[PageContent]:
        """Extract text from a DOCX file. Treats entire document as one page."""
        filename = Path(file_path).name
        pages = []

        try:
            doc = DocxDocument(file_path)
            # Collect all paragraph text
            full_text = []
            for para in doc.paragraphs:
                text = para.text.strip()
                if text:
                    full_text.append(text)

            if full_text:
                pages.append(PageContent(
                    text="\n\n".join(full_text),
                    page_number=1,
                    source_file=filename
                ))

            logger.info(f"Extracted {len(full_text)} paragraphs from DOCX: {filename}")
        except Exception as e:
            logger.error(f"Error extracting DOCX {filename}: {e}")
            raise

        return pages


class TXTExtractor(TextExtractor):
    """Extracts text from plain text files."""

    def extract(self, file_path: str) -> list[PageContent]:
        """Read entire text file as a single page."""
        filename = Path(file_path).name
        pages = []

        try:
            text = Path(file_path).read_text(encoding="utf-8").strip()
            if text:
                pages.append(PageContent(
                    text=text,
                    page_number=1,
                    source_file=filename
                ))
            logger.info(f"Extracted text from TXT: {filename} ({len(text)} chars)")
        except Exception as e:
            logger.error(f"Error extracting TXT {filename}: {e}")
            raise

        return pages


class CSVExtractor(TextExtractor):
    """Extracts schema and sample data from CSV files for RAG fallback."""

    def extract(self, file_path: str) -> list[PageContent]:
        filename = Path(file_path).name
        try:
            import pandas as pd
            df = pd.read_csv(file_path)
            text = f"Dataset: {filename}\nColumns: {', '.join(df.columns)}\nRows: {len(df)}\n\nSample Data:\n{df.head(5).to_string()}"
            logger.info(f"Extracted CSV for RAG: {filename}")
            return [PageContent(text=text, page_number=1, source_file=filename)]
        except Exception as e:
            logger.error(f"Error extracting CSV {filename}: {e}")
            raise


class XLSXExtractor(TextExtractor):
    """Extracts schema and sample data from XLSX files for RAG fallback."""

    def extract(self, file_path: str) -> list[PageContent]:
        filename = Path(file_path).name
        try:
            import pandas as pd
            df = pd.read_excel(file_path)
            text = f"Dataset: {filename}\nColumns: {', '.join(df.columns)}\nRows: {len(df)}\n\nSample Data:\n{df.head(5).to_string()}"
            logger.info(f"Extracted XLSX for RAG: {filename}")
            return [PageContent(text=text, page_number=1, source_file=filename)]
        except Exception as e:
            logger.error(f"Error extracting XLSX {filename}: {e}")
            raise


# --- Factory ---

_EXTRACTORS = {
    ".pdf": PDFExtractor,
    ".docx": DOCXExtractor,
    ".txt": TXTExtractor,
    ".csv": CSVExtractor,
    ".xlsx": XLSXExtractor,
}


def get_extractor(file_type: str) -> TextExtractor:
    """
    Get the appropriate text extractor for a file type.

    Args:
        file_type: File extension (e.g., '.pdf', '.docx', '.txt').

    Returns:
        An instance of the appropriate TextExtractor.

    Raises:
        ValueError: If file type is not supported.
    """
    file_type = file_type.lower()
    if file_type not in _EXTRACTORS:
        raise ValueError(f"Unsupported file type: {file_type}")
    return _EXTRACTORS[file_type]()
