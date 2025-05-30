from functools import lru_cache
from fastapi import Depends
from redis.asyncio import ConnectionPool, Redis
from .settings import get_settings
from httpx import AsyncClient
from contextlib import asynccontextmanager
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

@lru_cache(maxsize=1)
def get_redis_pool() -> ConnectionPool:
    settings = get_settings()
    return ConnectionPool.from_url(
        str(settings.REDIS_URL), max_connections=settings.REDIS_POOL_SIZE
    )

async def get_redis(
    pool: ConnectionPool = Depends(get_redis_pool)
) -> AsyncGenerator[Redis, None]:
    redis = Redis(connection_pool=pool)
    try:
        yield redis
    finally:
        await redis.close()

@lru_cache(maxsize=1)
def get_httpx_client() -> AsyncClient:
    settings = get_settings()
    return AsyncClient(timeout=settings.HTTP_TIMEOUT)

# Optional: context manager for non-FastAPI use
@asynccontextmanager
async def get_redis_conn(
    pool: ConnectionPool = Depends(get_redis_pool)
) -> AsyncGenerator[Redis, None]:
    redis = Redis(connection_pool=pool)
    try:
        yield redis
    finally:
        await redis.close()
