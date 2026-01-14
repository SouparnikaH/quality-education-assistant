#!/usr/bin/env python3
"""
Simple startup script for Render deployment.
This ensures the FastAPI app starts correctly on Render.
"""
import os
import uvicorn
from main import app

if __name__ == "__main__":
    # Get port from Render's environment variable
    port = int(os.getenv("PORT", 8000))
    print(f"Starting server on port {port}")

    # Start the server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
