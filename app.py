"""
Entry point for Hugging Face Spaces or simple local execution.
"""
import uvicorn
from backend.main import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
