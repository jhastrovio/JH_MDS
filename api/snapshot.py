from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from redis.asyncio import Redis

from .deps import get_redis
from .schemas import SnapshotRequest

router = APIRouter()


async def _trigger_snapshot(symbols: list[str], redis: Redis) -> None:
    for symbol in symbols:
        key = f"ticks:{symbol}"
        data = await redis.lrange(key, 0, -1)
        # Placeholder for persistence to storage layer
        print(f"Snapshot {symbol}: {len(data)} ticks")


@router.post("/snapshot", status_code=202)
async def snapshot(
    payload: SnapshotRequest,
    background: BackgroundTasks,
    redis: Redis = Depends(get_redis),
) -> None:
    if not payload.symbols:
        raise HTTPException(status_code=400, detail="symbols required")
    background.add_task(_trigger_snapshot, payload.symbols, redis)
