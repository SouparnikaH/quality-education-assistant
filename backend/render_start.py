#!/usr/bin/env python3
"""
Render startup script for FastAPI backend.
Handles PORT environment variable and binds to 0.0.0.0 for Render deployment.
"""
import os
import sys
import uvicorn

# Add the current directory to Python path so we can import from app/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import app

if __name__ == "__main__":
    # Get port from environment variable (Render provides this)
    port = int(os.getenv("PORT", 8000))

    # Bind to 0.0.0.0 for Render (not localhost)
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
