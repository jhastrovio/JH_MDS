from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from redis.asyncio import Redis

from .deps import get_redis
from .schemas import PriceResponse

router = APIRouter()


@router.get("/price", response_model=PriceResponse)
async def get_price(symbol: str, redis: Redis = Depends(get_redis)) -> PriceResponse:
    key = f"price:{symbol}"
    data = await redis.hgetall(key)
    if not data:
        raise HTTPException(status_code=404, detail="Price not found")
    return PriceResponse(
        symbol=symbol, price=float(data["price"]), timestamp=data["timestamp"]
    )
