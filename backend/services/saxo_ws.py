# backend/services/saxo_ws.py
"""
FX streaming via SaxoBank WebSockets, persisting ticks to Redis.
"""

import json
import asyncio
from datetime import datetime, timezone
from typing import Iterable

import websockets
from pydantic import BaseModel
from redis.asyncio import Redis
from fastapi import HTTPException

from core.settings import Settings, get_settings
from core.deps import get_logger, get_httpx_client
from services.oauth_client import SaxoOAuthClient

# === Module-level singletons via DI ===
settings: Settings = get_settings()
logger = get_logger()
http_client = get_httpx_client()
# Instantiate Redis pool once at module load
redis_pool = Redis.from_url(
    str(settings.REDIS_URL),
    max_connections=settings.REDIS_POOL_SIZE
)

# Separate Redis client for OAuth state if needed
oauth_redis = Redis(connection_pool=redis_pool)
oauth_client = SaxoOAuthClient(
    settings=settings,
    logger=logger,
    client=http_client,
    redis=oauth_redis,
)

# === Constants ===
REDIS_TTL_SECONDS = 30
MAX_TICKS_PER_SYMBOL = 100
WS_URL = "wss://streaming.saxobank.com/openapi/streamingws/connect"
API_BASE = "https://gateway.saxobank.com/openapi"

SYMBOL_TO_UIC = {
    "EUR-USD": 21,
    "GBP-USD": 31,
    "USD-JPY": 42,
    "AUD-USD": 4,
    "USD-CHF": 39,
    "USD-CAD": 38,
    "NZD-USD": 37,
}


class SaxoTick(BaseModel):
    symbol: str
    bid: float
    ask: float
    timestamp: str


async def _create_subscription(symbol: str, context_id: str, token: str) -> str:
    """Create HTTP subscription for a symbol and return reference ID."""
    uic = SYMBOL_TO_UIC.get(symbol)
    if not uic:
        raise ValueError(f"Unknown symbol: {symbol}")

    reference_id = f"{symbol.replace('-', '_')}_sub"
    payload = {
        "Arguments": {"AssetType": "FxSpot", "Uic": uic},
        "ContextId": context_id,
        "ReferenceId": reference_id,
        "RefreshRate": 1000,
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    resp = await http_client.post(
        f"{API_BASE}/trade/v1/prices/subscriptions",
        json=payload,
        headers=headers,
    )
    if resp.status_code == 201:
        return reference_id

    error_text = await resp.text()
    logger.error(
        "Subscription failed for %s: %s – %s",
        symbol,
        resp.status_code,
        error_text,
    )
    raise RuntimeError(
        f"Subscription failed for {symbol}: {resp.status_code} – {error_text}"
    )


async def _connect(token: str) -> websockets.WebSocketClientProtocol:
    """Open a WebSocket connection to Saxo’s streaming endpoint."""
    context_id = "mds"
    url = f"{WS_URL}?contextId={context_id}"
    headers = {"Authorization": f"Bearer {token}"}
    return await websockets.connect(url, extra_headers=headers)


async def stream_quotes(symbols: Iterable[str], redis: Redis) -> None:
    """
    Subscribe to Saxo streaming and persist ticks to Redis.

    Retries on disconnect with exponential backoff. Closes OAuth Redis at end.
    """
    token = await oauth_client.get_valid_token()
    backoff = 1

    try:
        while True:
            try:
                logger.info("📡 Subscribing to %d symbols", len(symbols))
                refs = []
                for s in symbols:
                    try:
                        ref = await _create_subscription(s, "mds", token)
                        refs.append(ref)
                        logger.info("✅ Subscribed to %s", s)
                    except Exception as e:
                        logger.error("❌ Failed to subscribe %s: %s", s, e)

                if not refs:
                    raise RuntimeError("No subscriptions succeeded")

                async with await _connect(token) as ws:
                    logger.info("🔗 WebSocket connected")
                    backoff = 1

                    async for raw in ws:
                        try:
                            if len(raw) < 16:
                                continue
                            ref_size = raw[10]
                            if len(raw) < 11 + ref_size + 5:
                                continue
                            ref_id = raw[11 : 11 + ref_size].decode("ascii")
                            payload_size = int.from_bytes(
                                raw[12 + ref_size : 16 + ref_size], "little"
                            )
                            if len(raw) < 16 + ref_size + payload_size:
                                continue

                            payload = raw[16 + ref_size : 16 + ref_size + payload_size]
                            data = json.loads(payload.decode("utf-8"))
                            quote = data.get("Quote")
                            if not quote or "Bid" not in quote or "Ask" not in quote:
                                continue

                            symbol = ref_id.replace("_sub", "").replace("_", "-")
                            tick = SaxoTick(
                                symbol=symbol,
                                bid=float(quote["Bid"]),
                                ask=float(quote["Ask"]),
                                timestamp=data.get("LastUpdated", datetime.utcnow().isoformat()),  # fallback
                            )
                            logger.debug("📊 %s bid/ask %s/%s", symbol, tick.bid, tick.ask)

                            serialized = tick.json()
                            key = f"fx:{symbol}"
                            await redis.set(key, serialized, ex=REDIS_TTL_SECONDS)

                            list_key = f"ticks:{symbol}"
                            await redis.lpush(list_key, serialized)
                            await redis.ltrim(list_key, 0, MAX_TICKS_PER_SYMBOL - 1)
                            await redis.expire(list_key, REDIS_TTL_SECONDS)

                        except (json.JSONDecodeError, KeyError, ValueError):
                            continue

                break  # normal exit

            except (websockets.WebSocketException, OSError) as e:
                logger.warning("⚠️ Connection error: %s, retrying in %ds", e, backoff)
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 16)

            except asyncio.CancelledError:
                break

    finally:
        await oauth_redis.close()
        logger.info("🚪 OAuth Redis client closed")
