"""
Enterprise AI Copilot - Application Configuration

Loads environment variables and provides centralized configuration
for all application modules.
"""

import os
from pathlib import Path
from functools import lru_cache

from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- Application ---
    APP_NAME: str = "Enterprise AI Copilot"
    DEBUG: bool = False

    # --- LLM Configuration ---
    GROQ_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    LLM_PROVIDER: str = "groq"  # "groq" or "openai"
    LLM_MODEL: str = "llama-3.3-70b-versatile"

    # --- Embeddings ---
    EMBEDDING_MODEL: str = "BAAI/bge-base-en-v1.5"

    # --- Paths ---
    UPLOAD_DIR: str = str(BASE_DIR / "uploads")
    VECTOR_STORE_DIR: str = str(BASE_DIR / "vector_db")
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'enterprise_copilot.db'}"

    # --- Authentication ---
    JWT_SECRET: str = "change_this_to_a_strong_random_secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    # --- Upload Limits ---
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: list[str] = [".pdf", ".docx", ".txt", ".csv", ".xlsx"]

    # --- RAG Defaults ---
    DEFAULT_TEMPERATURE: float = 0.3
    DEFAULT_MAX_TOKENS: int = 2048
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    RETRIEVER_K: int = 4

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
