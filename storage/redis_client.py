from __future__ import annotations

import os
from redis.asyncio import Redis


def get_redis() -> Redis:
    """Return an asyncio Redis client configured from ``REDIS_URL`` env var."""
    url = os.environ.get("REDIS_URL")
    if not url:
        raise RuntimeError("REDIS_URL not set")
    return Redis.from_url(url, encoding="utf-8", decode_responses=True)
