from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from redis.asyncio import Redis

from .deps import get_redis
from .schemas import Tick


def _parse_tick(raw: str) -> Tick:
    if hasattr(Tick, "model_validate_json"):
        return Tick.model_validate_json(raw)
    return Tick.parse_raw(raw)


router = APIRouter()


@router.get("/ticks", response_model=List[Tick])
async def get_ticks(symbol: str, redis: Redis = Depends(get_redis)) -> List[Tick]:
    key = f"ticks:{symbol}"
    data = await redis.lrange(key, 0, -1)
    if not data:
        raise HTTPException(status_code=404, detail="No ticks found")
    ticks = [_parse_tick(item) for item in data]
    return ticks
