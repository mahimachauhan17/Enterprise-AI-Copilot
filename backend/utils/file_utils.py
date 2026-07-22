"""
File Utilities

Helper functions for file validation, saving, and management.
"""

import uuid
from pathlib import Path

from fastapi import UploadFile

from backend.config import get_settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


def validate_file_type(filename: str) -> bool:
    """
    Check if a file has an allowed extension.

    Args:
        filename: The original filename to validate.

    Returns:
        True if the extension is allowed, False otherwise.
    """
    ext = Path(filename).suffix.lower()
    return ext in settings.ALLOWED_EXTENSIONS


def get_file_extension(filename: str) -> str:
    """
    Get the lowercase file extension.

    Args:
        filename: The filename.

    Returns:
        Lowercase extension (e.g., '.pdf').
    """
    return Path(filename).suffix.lower()


async def save_upload_file(file: UploadFile, upload_dir: str) -> tuple[str, str]:
    """
    Save an uploaded file to disk with a unique name.

    Args:
        file: The FastAPI UploadFile object.
        upload_dir: Directory to save the file in.

    Returns:
        Tuple of (saved_filename, full_file_path).
    """
    ensure_directory(upload_dir)

    # Generate unique filename to avoid collisions
    ext = get_file_extension(file.filename)
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = Path(upload_dir) / unique_name

    # Write file content
    content = await file.read()
    file_path.write_bytes(content)

    logger.info(f"Saved file: {file.filename} -> {unique_name} ({len(content)} bytes)")

    return unique_name, str(file_path)


def get_file_size_bytes(file_path: str) -> int:
    """
    Get file size in bytes.

    Args:
        file_path: Path to the file.

    Returns:
        File size in bytes.
    """
    return Path(file_path).stat().st_size


def get_file_size_mb(file_path: str) -> float:
    """
    Get file size in megabytes.

    Args:
        file_path: Path to the file.

    Returns:
        File size in MB.
    """
    return get_file_size_bytes(file_path) / (1024 * 1024)


def ensure_directory(path: str) -> None:
    """
    Create a directory if it does not exist.

    Args:
        path: Directory path to ensure exists.
    """
    Path(path).mkdir(parents=True, exist_ok=True)


def delete_file(file_path: str) -> bool:
    """
    Delete a file from disk.

    Args:
        file_path: Path to the file to delete.

    Returns:
        True if file was deleted, False if it didn't exist.
    """
    path = Path(file_path)
    if path.exists():
        path.unlink()
        logger.info(f"Deleted file: {file_path}")
        return True
    logger.warning(f"File not found for deletion: {file_path}")
    return False
