from __future__ import annotations

import asyncio
import json
from typing import Iterable

from redis.asyncio import Redis
from websockets import connect


async def stream_prices(symbols: Iterable[str], redis: Redis) -> None:
    uri = "wss://example.saxo.com/prices"  # placeholder
    async with connect(uri) as ws:
        await ws.send(json.dumps({"type": "subscribe", "symbols": list(symbols)}))
        async for message in ws:
            data = json.loads(message)
            symbol = data["symbol"]
            await redis.hset(
                f"price:{symbol}",
                mapping={"price": data["price"], "timestamp": data["timestamp"]},
            )
            await redis.expire(f"price:{symbol}", 30)
            await redis.lpush(f"ticks:{symbol}", json.dumps(data))
            await redis.ltrim(f"ticks:{symbol}", 0, 1000)
            await redis.expire(f"ticks:{symbol}", 30)
            await asyncio.sleep(0)  # yield control
