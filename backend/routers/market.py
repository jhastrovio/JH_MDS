from fastapi import APIRouter, Depends, HTTPException
from core.deps import get_settings, get_logger, get_redis
from redis.asyncio import Redis
from services.market_data import fetch_price, fetch_ticks

# Singleton logger
logger = get_logger()

router = APIRouter(prefix="/market", tags=["market"])

@router.get("/price/{symbol}")
async def get_price(
    symbol: str,
    redis=Depends(get_redis),
    settings=Depends(get_settings),
    logger=Depends(get_logger),
):
    price = await fetch_price(symbol, redis, settings)
    if price is None:
        raise HTTPException(status_code=404, detail="Symbol not found")
    return price

@router.get("/ticks/{symbol}")
async def get_ticks(
    symbol: str,
    redis=Depends(get_redis),
    settings=Depends(get_settings),
    logger=Depends(get_logger),
):
    ticks = await fetch_ticks(symbol, redis, settings)
    if not ticks:
        raise HTTPException(status_code=404, detail="No ticks available")
    return ticks