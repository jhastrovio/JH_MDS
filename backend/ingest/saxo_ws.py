"""Utilities for streaming foreign exchange quotes from Saxo via WebSockets.

The module exposes a small wrapper around Saxo's streaming API that forwards
incoming ticks to Redis for short-term caching. Functions are asynchronous and
designed to run in a serverless environment.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Iterable
import asyncio
from pathlib import Path

import websockets
import aiohttp
from pydantic import BaseModel
from redis.asyncio import Redis

# Add parent directory to path for imports
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

REDIS_TTL_SECONDS = 30
MAX_TICKS_PER_SYMBOL = 100
WS_URL = "wss://streaming.saxobank.com/openapi/streamingws/connect"
API_BASE = "https://gateway.saxobank.com/openapi"

# Symbol to UIC mapping for common FX pairs
SYMBOL_TO_UIC = {
    "EUR-USD": 21,
    "GBP-USD": 22, 
    "USD-JPY": 23,
    "AUD-USD": 24,
    "USD-CHF": 25,
    "USD-CAD": 26,
    "NZD-USD": 27
}


class SaxoTick(BaseModel):
    symbol: str
    bid: float
    ask: float
    timestamp: str


async def _get_oauth_token() -> str:
    """Get valid OAuth token from the OAuth client or Redis."""
    try:
        # First try to get token from OAuth client (if running in same process)
        from app.oauth import oauth_client
        return await oauth_client.get_valid_token()
    except ImportError:
        # If OAuth client not available, try to load token from Redis
        try:
            from storage.redis_client import get_redis
            redis = get_redis()
            try:
                token_data_raw = await redis.get("saxo:current_token")
                if token_data_raw:
                    token_data = json.loads(token_data_raw)
                    access_token = token_data.get("access_token")
                    if access_token:
                        print(f"SAXO WS: Using OAuth token from Redis")
                        return access_token
            finally:
                await redis.close()
        except Exception as e:
            print(f"SAXO WS: Failed to load token from Redis: {e}")
        
        # Fallback to environment variable for standalone testing
        token = os.environ.get("SAXO_API_TOKEN")
        if not token:
            raise RuntimeError("No OAuth token available: OAuth client not accessible, no token in Redis, and SAXO_API_TOKEN not set")
        print(f"SAXO WS: Using token from environment variable")
        return token


async def _create_subscription(symbol: str, context_id: str, token: str) -> str:
    """Create HTTP subscription for a symbol and return reference ID."""
    
    uic = SYMBOL_TO_UIC.get(symbol)
    if not uic:
        raise ValueError(f"Unknown symbol: {symbol}")
    
    reference_id = f"{symbol.replace('-', '_')}_sub"
    
    subscription_data = {
        "Arguments": {
            "AssetType": "FxSpot",
            "Uic": uic
        },
        "ContextId": context_id,
        "ReferenceId": reference_id,
        "RefreshRate": 1000
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        url = f"{API_BASE}/trade/v1/prices/subscriptions"
        async with session.post(url, json=subscription_data, headers=headers) as response:
            if response.status == 201:
                return reference_id
            else:
                error_text = await response.text()
                raise RuntimeError(f"Subscription failed for {symbol}: {response.status} - {error_text}")


async def _connect(token: str) -> websockets.WebSocketClientProtocol:
    """Open a WebSocket connection to the Saxo streaming endpoint."""
    
    # Use proper authentication and contextId
    context_id = "mds"
    url = f"{WS_URL}?contextId={context_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    return await websockets.connect(url, additional_headers=headers)


async def stream_quotes(symbols: Iterable[str], redis: Redis) -> None:
    """Subscribe to Saxo streaming and persist ticks to Redis.

    The connection is re-established with exponential backoff when interrupted.
    Both the latest tick and a capped list of recent ticks are stored. The Redis
    client is always closed on exit.
    """

    context_id = "mds"
    token = await _get_oauth_token()

    backoff = 1
    try:
        while True:
            try:
                # 1) Create HTTP subscriptions for all symbols
                print(f"📡 Creating subscriptions for {len(list(symbols))} symbols...")
                reference_ids = []
                for symbol in symbols:
                    try:
                        ref_id = await _create_subscription(symbol, context_id, token)
                        reference_ids.append(ref_id)
                        print(f"✅ Subscribed to {symbol}")
                    except Exception as e:
                        print(f"❌ Failed to subscribe to {symbol}: {e}")

                if not reference_ids:
                    raise RuntimeError("No successful subscriptions created")

                # 2) Connect to WebSocket and receive data
                async with await _connect(token) as ws:
                    print(f"🔗 WebSocket connected, waiting for data...")
                    backoff = 1

                    # 3) Read & parse ticks
                    async for raw in ws:
                        try:
                            # Parse the binary message format (see SaxoBank docs)
                            if len(raw) < 16:
                                continue
                                
                            # Extract reference ID and payload
                            ref_id_size = raw[10]
                            if len(raw) < 11 + ref_id_size + 5:
                                continue
                                
                            ref_id = raw[11:11+ref_id_size].decode('ascii')
                            payload_size = int.from_bytes(raw[12+ref_id_size:16+ref_id_size], 'little')
                            
                            if len(raw) < 16 + ref_id_size + payload_size:
                                continue
                                
                            payload = raw[16+ref_id_size:16+ref_id_size+payload_size]
                            data = json.loads(payload.decode('utf-8'))
                            
                            # Extract quote data if present
                            if "Quote" not in data:
                                continue
                            
                            quote = data["Quote"]
                            if "Ask" not in quote or "Bid" not in quote:
                                continue
                            
                            # Convert reference ID back to symbol
                            symbol = ref_id.replace("_sub", "").replace("_", "-")
                            
                            tick = SaxoTick(
                                symbol=symbol,
                                bid=float(quote["Bid"]),
                                ask=float(quote["Ask"]),
                                timestamp=data.get("LastUpdated", ""),
                            )
                            
                            print(f"📊 {symbol}: {tick.bid}/{tick.ask}")
                            
                            # Store in Redis
                            serialized = tick.model_dump_json()
                            key = f"fx:{tick.symbol}"
                            await redis.set(key, serialized, ex=REDIS_TTL_SECONDS)

                            list_key = f"ticks:{tick.symbol}"
                            await redis.lpush(list_key, serialized)
                            await redis.ltrim(list_key, 0, MAX_TICKS_PER_SYMBOL - 1)
                            await redis.expire(list_key, REDIS_TTL_SECONDS)
                            
                        except (json.JSONDecodeError, KeyError, ValueError) as e:
                            # Skip malformed messages
                            continue

                # Exit if the stream ends normally
                break

            except (websockets.WebSocketException, OSError, aiohttp.ClientError) as e:
                # 3) on error, back off and retry
                print(f"⚠️ Connection error: {e}, retrying in {backoff}s...")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 16)

            except asyncio.CancelledError:
                break

    finally:
        # 4) ensure Redis connection is closed
        await redis.close()
