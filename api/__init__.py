"""Main FastAPI application."""

from __future__ import annotations

from fastapi import FastAPI
from .auth.router import router as auth_router

app = FastAPI(title="JH Market Data API")

# Include all routers
app.include_router(auth_router)
