# backend/services/market_data.py
"""
Market Data Service - Continuous real-time data ingestion.
Uses centralized DI for settings, logging, and Redis.
"""

import asyncio
import signal
from datetime import datetime, timezone
from typing import List, Optional
import json

from fastapi import Depends, HTTPException
from redis.asyncio import Redis

from core.deps import get_redis, get_httpx_client, get_logger, get_settings
from core.settings import Settings
from models.market import PriceResponse, Tick

from services.saxo_ws import stream_quotes  # make sure you moved saxo_ws here

# Service configuration
FX_SYMBOLS: List[str] = [
    "EUR-USD", "GBP-USD", "USD-JPY", "AUD-USD",
    "USD-CHF", "USD-CAD", "NZD-USD"
]
RESTART_DELAY = 5               # seconds between restart attempts
MAX_RESTART_ATTEMPTS = 10
HEALTH_CHECK_INTERVAL = 30      # seconds

# Instantiate shared dependencies
logger = get_logger()


class MarketDataService:
    """Manages continuous market data ingestion with health monitoring."""

    def __init__(self):
        self.running = False
        self.restart_count = 0

    async def start(self):
        """Start the market data service."""
        logger.info("🚀 Starting Market Data Service")
        logger.info(f"📊 Symbols: {', '.join(FX_SYMBOLS)}")

        self.running = True

        # Set service status in Redis
        # (You must create a Redis client here if running as a script)
        settings = get_settings()
        self.redis = Redis.from_url(
            str(settings.REDIS_URL),
            max_connections=settings.REDIS_POOL_SIZE
        )

        await self._update_service_status("starting")

        # Start health monitoring task
        health_task = asyncio.create_task(self._health_monitor())

        try:
            while self.running and self.restart_count < MAX_RESTART_ATTEMPTS:
                try:
                    await self._update_service_status("running")
                    logger.info(
                        f"🔗 Connecting to SaxoBank WebSocket (attempt {self.restart_count + 1})"
                    )

                    # Run the streaming client
                    await stream_quotes(FX_SYMBOLS, self.redis)

                    # Normal exit
                    logger.info("📡 Stream ended normally")
                    break

                except Exception as e:
                    self.restart_count += 1
                    logger.error(
                        f"❌ Stream error (attempt {self.restart_count}): {e}",
                        exc_info=True
                    )

                    if self.restart_count >= MAX_RESTART_ATTEMPTS:
                        logger.error(
                            f"🛑 Max restart attempts ({MAX_RESTART_ATTEMPTS}) reached"
                        )
                        await self._update_service_status("failed")
                        break

                    await self._update_service_status("restarting")
                    logger.info(f"⏳ Restarting in {RESTART_DELAY} seconds...")
                    await asyncio.sleep(RESTART_DELAY)

        finally:
            health_task.cancel()
            await self._update_service_status("stopped")
            await self.redis.close()
            logger.info("🛑 Market Data Service stopped")

    async def stop(self):
        """Stop the market data service gracefully."""
        logger.info("🛑 Attempting to stop Market Data Service...")
        self.running = False
        logger.info("🛑 Market Data Service running flag set to False.")

    async def _health_monitor(self):
        """Monitor service health and update heartbeat in Redis."""
        logger.info("💓 Health monitor started.")
        while self.running:
            try:
                await asyncio.sleep(HEALTH_CHECK_INTERVAL)

                if not self.running:
                    logger.info(
                        "💓 Health monitor: self.running is false, exiting."
                    )
                    break

                now = datetime.now(timezone.utc)
                logger.info(f"💓 Health check at {now.isoformat()}")

                # Update heartbeat key
                await self.redis.set(
                    "service:market_data:heartbeat",
                    now.isoformat(),
                    ex=HEALTH_CHECK_INTERVAL + 5
                )
                logger.debug(
                    f"💓 Health check – restarts so far: {self.restart_count}"
                )

            except asyncio.CancelledError:
                logger.info("💓 Health monitor task cancelled.")
                break
            except Exception as e:
                logger.error("❌ Health monitor error", exc_info=True)

    async def _update_service_status(self, status: str):
        """Update overall service status in Redis."""
        try:
            payload = {
                "status": status,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "restart_count": self.restart_count,
                "symbols": FX_SYMBOLS,
            }
            await self.redis.set(
                "service:market_data:status",
                json.dumps(payload),
                ex=300
            )
        except Exception as e:
            logger.error(f"❌ Failed to update service status: {e}", exc_info=True)


# Example entrypoint for running as a standalone process
service = MarketDataService()


async def main_wrapper():
    """Entrypoint wrapper to handle graceful shutdown."""
    loop = asyncio.get_running_loop()
    stop_evt = asyncio.Event()

    def _signal_handler():
        logger.info("🔔 Received stop signal, shutting down...")
        stop_evt.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _signal_handler)

    # Run service.start() and also wait for a stop signal
    task = asyncio.create_task(service.start())
    await stop_evt.wait()
    await service.stop()
    task.cancel()
    logger.info("Service shutdown complete.")


async def fetch_price(
    symbol: str,
    redis: Redis = Depends(get_redis),
    settings = Depends(get_settings),
    logger = Depends(get_logger),
) -> PriceResponse:
    """
    Return the latest mid‐price for a symbol from Redis.
    """
    raw = await redis.get(f"fx:{symbol}")
    if not raw:
        raise HTTPException(status_code=404, detail="Symbol not found")
    data = json.loads(raw)
    tick = Tick(**data)
    price = (tick.bid + tick.ask) / 2
    return PriceResponse(symbol=tick.symbol, price=price, timestamp=tick.timestamp)


async def fetch_ticks(
    symbol: str,
    since: Optional[str] = None,
    redis: Redis = Depends(get_redis),
    settings = Depends(get_settings),
    logger = Depends(get_logger),
) -> List[Tick]:
    """
    Return a list of recent ticks for `symbol` from Redis, optionally filtered by `since`.
    """
    raw_list = await redis.lrange(f"ticks:{symbol}", 0, -1)
    ticks = [Tick.parse_raw(item) for item in raw_list]
    if since:
        cutoff = datetime.fromisoformat(since)
        ticks = [t for t in ticks if t.timestamp >= cutoff]
    return ticks
