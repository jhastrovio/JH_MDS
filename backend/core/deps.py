from functools import lru_cache
from fastapi import Depends
from redis.asyncio import ConnectionPool, Redis
from .settings import Settings, get_settings
from httpx import AsyncClient
from contextlib import asynccontextmanager
import logging


@lru_cache(maxsize=1)
def get_logger(settings: Settings = Depends(get_settings)) -> logging.Logger:
    logger = logging.getLogger("jh")
    handler = logging.StreamHandler()
    handler.setLevel(settings.LOG_LEVEL)
    logger.setLevel(settings.LOG_LEVEL)
    if not logger.handlers:
        logger.addHandler(handler)
    return logger

@lru_cache(maxsize=1)
def get_redis_pool(settings: Settings = Depends(get_settings)) -> ConnectionPool:
    return ConnectionPool.from_url(
        str(settings.REDIS_URL), max_connections=settings.REDIS_POOL_SIZE
    )

from typing import AsyncGenerator

async def get_redis(
    pool: ConnectionPool = Depends(get_redis_pool)
) -> AsyncGenerator[Redis, None]:
    redis = Redis(connection_pool=pool)
    try:
        yield redis
    finally:
        await redis.close()

@lru_cache(maxsize=1)
def get_httpx_client(
    settings: Settings = Depends(get_settings),
) -> AsyncClient:
    return AsyncClient(timeout=settings.HTTP_TIMEOUT)

@asynccontextmanager
async def get_redis_conn(pool=Depends(get_redis_pool)):
    redis = Redis(connection_pool=pool)
    try:
        yield redis
    finally:
        await redis.close()