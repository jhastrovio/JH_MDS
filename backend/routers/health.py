from fastapi import APIRouter, Depends
from routers.health import get_system_health
from core.deps import get_redis, get_settings, get_logger
from redis.asyncio import Redis

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/")
async def system_health(
    redis=Depends(get_redis),
    settings=Depends(get_settings),
    logger=Depends(get_logger),
):
    status = await get_system_health(redis, settings, logger)
    return status