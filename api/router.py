from __future__ import annotations

import json
import os
from typing import Any

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from market_data.models import PriceResponse, Tick
from storage.redis_client import get_redis
from storage.on_drive import upload_table

router = APIRouter(prefix="/api")

_bearer = HTTPBearer()


def _verify_jwt(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> None:
    secret = os.environ.get("JWT_SECRET")
    if not secret:
        raise HTTPException(status_code=500, detail="JWT_SECRET not configured")
    token = credentials.credentials
    try:
        jwt.decode(token, secret, algorithms=["HS256"])
    except JWTError:
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


@router.get("/ticks", response_model=list[Tick])
async def get_ticks(
    symbol: str,
    since: str | None = None,
    _: Any = Depends(_verify_jwt),
) -> list[Tick]:
    """Return cached ticks for ``symbol`` optionally filtered by ``since``."""
    redis = get_redis()
    key = f"ticks:{symbol}"
    raw_ticks = await redis.lrange(key, 0, -1)
    await redis.close()
    if not raw_ticks:
        raise HTTPException(status_code=404, detail="No ticks found")
    ticks = [Tick(**json.loads(item)) for item in raw_ticks]
    if since:
        try:
            cutoff = datetime.fromisoformat(since.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid since timestamp")
        ticks = [
            t
            for t in ticks
            if datetime.fromisoformat(t.timestamp.replace("Z", "+00:00")) >= cutoff
        ]
    return ticks


@router.post("/snapshot", status_code=status.HTTP_202_ACCEPTED)
async def create_snapshot(
    payload: dict[str, list[str]],
    _: Any = Depends(_verify_jwt),
) -> dict[str, str]:
    symbols = payload.get("symbols")
    if not symbols:
        raise HTTPException(status_code=400, detail="symbols required")
    redis = get_redis()
    rows = []
    for sym in symbols:
        raw = await redis.get(f"fx:{sym}")
        if not raw:
            continue
        data = json.loads(raw)
        rows.append(data)
    await redis.close()
    if not rows:
        raise HTTPException(status_code=404, detail="No data for symbols")
    import pyarrow as pa

    table = pa.Table.from_pylist(rows)
    now = datetime.utcnow().isoformat().replace(":", "-")
    path = f"snapshots/{now}.parquet"
    await upload_table(table, path)
    return {"detail": "snapshot scheduled", "path": path}
