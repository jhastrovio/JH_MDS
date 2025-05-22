from __future__ import annotations

import os
from contextlib import asynccontextmanager
from redis.asyncio import Redis


@asynccontextmanager
async def get_redis() -> Redis:
    url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    client = Redis.from_url(url, decode_responses=True)
    try:
        yield client
    finally:
        await client.close()
