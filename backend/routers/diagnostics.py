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
