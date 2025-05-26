from __future__ import annotations

from fastapi import FastAPI

from .router import router

app = FastAPI(title="JH Market Data API")
app.include_router(router, prefix="/api")
