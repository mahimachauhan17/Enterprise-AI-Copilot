"""
Enterprise AI Copilot - Database Configuration

SQLAlchemy engine, session management, and base model for SQLite.
"""

import logging
import re
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from typing import Generator

from backend.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# 1. Verify DATABASE_URL is loaded from .env and uses PostgreSQL
# if not settings.DATABASE_URL or settings.DATABASE_URL.startswith("sqlite"):
#     logger.error("FATAL: DATABASE_URL is missing or using SQLite. Ensure .env is loaded correctly and points to PostgreSQL.")
#     sys.exit(1)

# Ensure psycopg2 is used explicitly if not specified in the scheme
if settings.DATABASE_URL.startswith("postgres://"):
    settings.DATABASE_URL = settings.DATABASE_URL.replace("postgres://", "postgresql://", 1)

# 2. Print the database engine URL at startup (mask password)
def mask_db_url(url: str) -> str:
    """Mask the password in the database URL."""
    return re.sub(r":([^:@]+)@", ":***@", url)

masked_url = mask_db_url(settings.DATABASE_URL)
print(f"--- DATABASE INITIALIZATION ---")
print(f"Connecting to Database: {masked_url}")

connect_args = {}
# PostgreSQL specific connection arguments (e.g. for Supabase pooler)
if "supabase.co" in settings.DATABASE_URL or "supabase.com" in settings.DATABASE_URL:
    # Use sslmode=require for Supabase
    connect_args["sslmode"] = "require"

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=True,  # Turn on echo to see SQLAlchemy logs
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all database tables."""
    print("--- IMPORTING MODELS ---")
    try:
        # 4. Import every SQLAlchemy model before Base.metadata.create_all() is executed.
        from backend.models.user import User
        from backend.models.document import Document
        from backend.models.chat import Conversation, Message
        print("Models imported successfully.")
    except Exception as e:
        print(f"Error importing models: {e}")
        raise e

    print("--- CREATING TABLES ---")
    try:
        # 5. Ensure Base.metadata.create_all(bind=engine) runs successfully
        Base.metadata.create_all(bind=engine)
        print("--- SCHEMA CREATION COMPLETE ---")
    except Exception as e:
        print(f"--- POSTGRESQL EXCEPTION DURING SCHEMA CREATION ---")
        print(f"Exception: {e}")
        raise e

