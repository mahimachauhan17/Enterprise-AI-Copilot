"""
Enterprise AI Copilot - FastAPI Application Entry Point

Initializes the FastAPI app, mounts static files, includes
API routers, and sets up startup events.
"""

from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.config import get_settings, BASE_DIR
from backend.database import init_db
from backend.api.auth import router as auth_router
from backend.api.documents import router as documents_router
from backend.api.chat import router as chat_router
from backend.utils.logger import get_logger
from backend.utils.file_utils import ensure_directory

logger = get_logger(__name__)
settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database and required directories on startup."""
    logger.info(f"Starting {settings.APP_NAME}...")

    # Initialize database tables
    init_db()
    logger.info("Database initialized")

    # Ensure upload directory exists
    ensure_directory(settings.UPLOAD_DIR)
    ensure_directory(settings.VECTOR_STORE_DIR)
    logger.info("Directories verified")

    logger.info(f"LLM Provider: {settings.LLM_PROVIDER} | Model: {settings.LLM_MODEL}")
    logger.info(f"Embedding Model: {settings.EMBEDDING_MODEL}")
    logger.info(f"{settings.APP_NAME} is ready!")
    yield

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Enterprise RAG application for intelligent document Q&A",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(chat_router)

# Mount frontend static files
frontend_dir = BASE_DIR / "frontend"
if frontend_dir.exists():
    app.mount("/css", StaticFiles(directory=str(frontend_dir / "css")), name="css")
    app.mount("/js", StaticFiles(directory=str(frontend_dir / "js")), name="js")
    assets_dir = frontend_dir / "assets"
    if not assets_dir.exists():
        assets_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")





# --- Frontend Routes ---

@app.get("/")
async def serve_login():
    """Serve the login page."""
    return FileResponse(str(frontend_dir / "index.html"))


@app.get("/signup")
async def serve_signup():
    """Serve the signup page."""
    return FileResponse(str(frontend_dir / "signup.html"))


@app.get("/dashboard")
async def serve_dashboard():
    """Serve the dashboard page."""
    return FileResponse(str(frontend_dir / "dashboard.html"))
