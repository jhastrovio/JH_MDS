"""Market Data Service - Continuous real-time data ingestion.

This service runs the SaxoBank WebSocket client continuously with:
- Automatic reconnection on failures
- Health monitoring
- Graceful shutdown handling
- Service status tracking
"""

import asyncio
import logging
import signal
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Set

# Add backend directory to path
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from ingest.saxo_ws import stream_quotes
from storage.redis_client import get_redis

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('market_data_service.log')
    ]
)
logger = logging.getLogger(__name__)

# Service configuration
FX_SYMBOLS = [
    'EUR-USD', 'GBP-USD', 'USD-JPY', 'AUD-USD', 
    'USD-CHF', 'USD-CAD', 'NZD-USD'
]

RESTART_DELAY = 5  # seconds between restart attempts
MAX_RESTART_ATTEMPTS = 10
HEALTH_CHECK_INTERVAL = 30  # seconds


class MarketDataService:
    """Manages continuous market data ingestion with health monitoring."""
    
    def __init__(self):
        self.running = False
        self.restart_count = 0
        self.last_data_time = None
        self.redis = None
        
    async def start(self):
        """Start the market data service."""
        logger.info("🚀 Starting Market Data Service")
        logger.info(f"📊 Symbols: {', '.join(FX_SYMBOLS)}")
        
        self.running = True
        self.redis = get_redis()
        
        # Set service status in Redis
        await self._update_service_status("starting")
        
        # Start health monitoring task
        health_task = asyncio.create_task(self._health_monitor())
        
        # Start main ingestion loop
        try:
            while self.running and self.restart_count < MAX_RESTART_ATTEMPTS:
                try:
                    await self._update_service_status("running")
                    logger.info(f"🔗 Connecting to SaxoBank WebSocket (attempt {self.restart_count + 1})")
                    
                    # Run the streaming client
                    await stream_quotes(FX_SYMBOLS, self.redis)
                    
                    # If we get here, the stream ended normally
                    logger.info("📡 Stream ended normally")
                    break
                    
                except Exception as e:
                    self.restart_count += 1
                    logger.error(f"❌ Stream error (attempt {self.restart_count}): {e}")
                    
                    if self.restart_count >= MAX_RESTART_ATTEMPTS:
                        logger.error(f"🛑 Max restart attempts ({MAX_RESTART_ATTEMPTS}) reached")
                        await self._update_service_status("failed")
                        break
                    
                    await self._update_service_status("restarting")
                    logger.info(f"⏳ Restarting in {RESTART_DELAY} seconds...")
                    await asyncio.sleep(RESTART_DELAY)
                    
        finally:
            # Cleanup
            health_task.cancel()
            await self._update_service_status("stopped")
            if self.redis:
                await self.redis.close()
            logger.info("🛑 Market Data Service stopped")
    
    async def stop(self):
        """Stop the market data service."""
        logger.info("🛑 Stopping Market Data Service...")
        self.running = False
        
    async def _health_monitor(self):
        """Monitor service health and update status."""
        while self.running:
            try:
                await asyncio.sleep(HEALTH_CHECK_INTERVAL)
                
                if not self.running:
                    break
                    
                # Check if we're receiving data
                current_time = datetime.now(timezone.utc)
                
                # Update heartbeat
                await self.redis.set(
                    "service:market_data:heartbeat", 
                    current_time.isoformat(),
                    ex=60
                )
                
                logger.debug(f"💓 Health check - Service running, restarts: {self.restart_count}")
                
            except Exception as e:
                logger.error(f"❌ Health monitor error: {e}")
    
    async def _update_service_status(self, status: str):
        """Update service status in Redis."""
        try:
            status_data = {
                "status": status,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "restart_count": self.restart_count,
                "symbols": FX_SYMBOLS
            }
            
            await self.redis.set(
                "service:market_data:status",
                str(status_data).replace("'", '"'),  # Simple JSON-like format
                ex=300  # 5 minutes TTL
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to update service status: {e}")


# Global service instance
service = MarketDataService()


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info(f"📡 Received signal {signum}, shutting down...")
    asyncio.create_task(service.stop())


async def main():
    """Main entry point."""
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await service.start()
    except KeyboardInterrupt:
        logger.info("📡 Keyboard interrupt received")
    except Exception as e:
        logger.error(f"❌ Service error: {e}")
    finally:
        await service.stop()


if __name__ == "__main__":
    asyncio.run(main()) 