# backend/api/index.py

import sys
import os
from pathlib import Path

# Add the parent directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import app

# Standard Vercel serverless handler
def handler(event, context):
    """
    Vercel serverless function handler for FastAPI app
    """
    # Return the FastAPI app instance directly
    # Vercel will handle the ASGI adapter
    return app
