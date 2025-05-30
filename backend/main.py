#!/usr/bin/env python3
"""
Backend startup script - handles Python path setup and runs the FastAPI server.
"""
import sys
import os
from pathlib import Path

# Add the backend directory to Python path so imports work correctly
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Import after path setup
import uvicorn
from app import create_app

if __name__ == "__main__":
    app = create_app()
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[str(backend_dir)]
    )
