"""Utilities for streaming foreign exchange quotes from Saxo via WebSockets.

The module exposes a small wrapper around Saxo's streaming API that forwards
incoming ticks to Redis for short-term caching. Functions are asynchronous and
designed to run in a serverless environment.
"""

from __future__ import annotations

import json
import os
from typing import Iterable

import websockets
from pydantic import BaseModel
from redis.asyncio import Redis

REDIS_TTL_SECONDS = 30
MAX_TICKS_PER_SYMBOL = 100
WS_URL = "wss://gateway.saxoapi.com/sim/openapi/streamingws/connect"


class SaxoTick(BaseModel):
    symbol: str
    bid: float
    ask: float
    timestamp: str


async def _connect() -> websockets.WebSocketClientProtocol:
    """Open a WebSocket connection to the Saxo streaming endpoint.

    Returns
    -------
    websockets.WebSocketClientProtocol
        A connected WebSocket client ready for sending and receiving
        streaming messages.
    """

    token = os.environ.get("SAXO_API_TOKEN")
    if not token:
        raise RuntimeError("SAXO_API_TOKEN not set")
    url = f"{WS_URL}?authorization=Bearer%20{token}"  # simple query-style auth
    return await websockets.connect(url)


async def stream_quotes(symbols: Iterable[str], redis: Redis) -> None:
    """Subscribe to Saxo streaming and persist ticks to Redis."""
    async with await _connect() as ws:
        await ws.send(json.dumps({"ContextId": "mds", "Instruments": list(symbols)}))
        async for raw in ws:
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if "Symbol" not in data:
                continue
            tick = SaxoTick(
                symbol=data["Symbol"],
                bid=float(data.get("Bid", 0)),
                ask=float(data.get("Ask", 0)),
                timestamp=data.get("TimeStamp", ""),
            )
            key = f"fx:{tick.symbol}"
            serialized = tick.model_dump_json()
            await redis.set(key, serialized, ex=REDIS_TTL_SECONDS)

            list_key = f"ticks:{tick.symbol}"
            await redis.lpush(list_key, serialized)
            await redis.ltrim(list_key, 0, MAX_TICKS_PER_SYMBOL - 1)
            await redis.expire(list_key, REDIS_TTL_SECONDS)
