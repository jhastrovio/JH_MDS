"""
Adapter for FastAPI applications to work smoothly with Vercel serverless functions.
"""
from typing import Callable
from fastapi import FastAPI

def create_handler(app: FastAPI) -> Callable:
    """
    Create a handler function that Vercel can use to process requests.
    
    This ensures proper ASGI protocol compliance for Vercel's Python runtime.
    
    Args:
        app: The FastAPI application instance
        
    Returns:
        A handler function compatible with Vercel serverless
    """
    async def handler(req, context):
        # This is the handler that Vercel serverless functions expect
        return await app(req, context)
    
    return handler
