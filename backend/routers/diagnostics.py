# backend/routers/diagnostics.py

from fastapi import APIRouter, Depends
from core.monitoring import get_system_health # Changed from routers.health
from core.deps import get_settings, get_logger, get_redis # Removed get_httpx_client as it's unused
from redis.asyncio import Redis

# Singleton logger
logger = get_logger()

router = APIRouter(prefix="/debug", tags=["diagnostics"])

@router.get("/readiness")
async def readiness(
    redis=Depends(get_redis),
    settings=Depends(get_settings),
    logger=Depends(get_logger),
):
    summary = await get_system_health(redis, settings, logger)
    # Only include minimal checks for readiness
    return { "redis": summary.get("redis"), "uptime": summary.get("uptime") }

@router.get("/metrics")
async def metrics(
    # Integrate with Prometheus client here
):
    return "TODO: Prometheus metrics output"

@router.get("/redis-data", summary="Get latest Redis FX data for all symbols")
async def redis_data(
    redis: Redis = Depends(get_redis),
):
    """
    Returns the latest FX price data and timestamps for all tracked symbols in Redis.
    """
    from services.market_data import FX_SYMBOLS
    import json
    from datetime import datetime, timezone

    results = []
    now = datetime.now(timezone.utc)
    for symbol in FX_SYMBOLS:
        raw = await redis.get(f"fx:{symbol}")
        if raw:
            data = json.loads(raw)
            ts = data.get("timestamp")
            age = None
            if ts:
                try:
                    dt = datetime.fromisoformat(ts)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    age = (now - dt).total_seconds()
                except Exception:
                    age = None
            results.append({
                "symbol": symbol,
                "price": data.get("bid") and data.get("ask") and (data["bid"] + data["ask"]) / 2,
                "timestamp": ts,
                "age_seconds": age,
                "raw": data
            })
        else:
            results.append({
                "symbol": symbol,
                "error": "No data in Redis"
            })
    return {"fx": results}
