from functools import lru_cache
from fastapi import Depends, Request
from redis.asyncio import Redis
from .settings import get_settings
from httpx import AsyncClient
import logging
from typing import AsyncGenerator

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

async def get_redis():
    settings = get_settings()
    redis = Redis.from_url(
        str(settings.REDIS_URL),
        max_connections=settings.REDIS_POOL_SIZE
    )
    try:
        yield redis
    finally:
        await redis.close()

@lru_cache(maxsize=1)
def get_httpx_client() -> AsyncClient:
    settings = get_settings()
    return AsyncClient(timeout=settings.HTTP_TIMEOUT)
