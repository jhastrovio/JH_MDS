from __future__ import annotations

import json
import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from market_data.models import PriceResponse, Tick
from storage.redis_client import get_redis

router = APIRouter(prefix="/api")

_bearer = HTTPBearer()


def _verify_jwt(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> None:
    secret = os.environ.get("JWT_SECRET")
    if not secret:
        raise HTTPException(status_code=500, detail="JWT_SECRET not configured")
    token = credentials.credentials
    if token != secret:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.get("/price", response_model=PriceResponse)
async def get_price(symbol: str, _: Any = Depends(_verify_jwt)) -> PriceResponse:
    redis = get_redis()
    key = f"fx:{symbol}"
    raw = await redis.get(key)
    await redis.close()
    if not raw:
        raise HTTPException(status_code=404, detail="Symbol not found")
    data = json.loads(raw)
    tick = Tick(**data)
    price = (tick.bid + tick.ask) / 2
    return PriceResponse(symbol=tick.symbol, price=price, timestamp=tick.timestamp)
