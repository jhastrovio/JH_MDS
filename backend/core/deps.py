from functools import lru_cache
from fastapi import Depends, Request
from redis.asyncio import Redis
from .settings import get_settings
from httpx import AsyncClient
import logging
from typing import AsyncGenerator
from fastapi import FastAPI

app = FastAPI()

@lru_cache(maxsize=1)
def get_logger() -> logging.Logger:
    settings = get_settings()
    logger = logging.getLogger("jh")
    handler = logging.StreamHandler()
    handler.setLevel(settings.LOG_LEVEL)
    logger.setLevel(settings.LOG_LEVEL)
    if not logger.handlers:
        logger.addHandler(handler)
    return logger

def get_redis(request: Request) -> Redis:
    """
    Return the application-wide Redis client stored on startup.
    """
    return request.app.state.redis

@lru_cache(maxsize=1)
def get_httpx_client() -> AsyncClient:
    settings = get_settings()
    return AsyncClient(timeout=settings.HTTP_TIMEOUT)

@app.on_event("shutdown")
async def shutdown_httpx():
    httpx_client = get_httpx_client()
    await httpx_client.aclose()
