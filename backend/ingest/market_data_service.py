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

# Define ROOT_DIR for absolute log path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent # JH-MDS directory

from ingest.saxo_ws import stream_quotes
from storage.redis_client import get_redis

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
        """Stop the market_data_service."""
        logger.info("🛑 Attempting to stop Market Data Service...")
        self.running = False
        # Ensure that stream_quotes is not called here.
        # The main loop in start() should exit, and cleanup will occur in its finally block.
        logger.info("🛑 Market Data Service running flag set to False.")

    async def _health_monitor(self):
        """Monitor service health and update status."""
        logger.info("💓 Health monitor started.")
        while self.running:
            try:
                await asyncio.sleep(HEALTH_CHECK_INTERVAL)
                
                if not self.running:
                    logger.info("💓 Health monitor: self.running is false, exiting loop.")
                    break
                    
                current_time = datetime.now(timezone.utc)
                logger.info(f"💓 Health check: Attempting to update heartbeat at {current_time.isoformat()}")
                
                # Update heartbeat
                await self.redis.set(
                    "service:market_data:heartbeat", 
                    current_time.isoformat(),
                    ex=60 # ex=60 means expire in 60 seconds
                )
                logger.info(f"💓 Heartbeat updated successfully in Redis at {current_time.isoformat()}")
                
                logger.debug(f"💓 Health check - Service running, restarts: {self.restart_count}") # Kept as debug
                
            except asyncio.CancelledError:
                logger.info("💓 Health monitor task cancelled.")
                break
            except Exception as e:
                logger.error(f"❌ Health monitor error: {e}", exc_info=True) # Add exc_info for full traceback
    
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


async def main_wrapper():
    """Wraps the main service start and handles graceful shutdown on KeyboardInterrupt."""
    try:
        await service.start()
    except asyncio.CancelledError:
        logger.info("Main task cancelled, shutting down.")
    # KeyboardInterrupt will be caught in the __main__ block
    finally:
        # Ensure stop is called if service was started and not stopped by KeyboardInterrupt handler
        if service.running: # Check if service was actually running
            logger.info("Service shutting down from main_wrapper finally block.")
            await service.stop() # Ensure stop is awaited
        logger.info("Service shutdown complete from main_wrapper.")


if __name__ == "__main__":
    # Simplified logging configuration directly here
    LOG_FILE_PATH = ROOT_DIR / "market_data_service.log"
    print(f"[MAIN] Attempting to configure logging to: {LOG_FILE_PATH}")

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE_PATH, encoding='utf-8'), # Specify UTF-8 encoding
            logging.StreamHandler() # Keep console output
        ],
        force=True
    )

    logger = logging.getLogger(__name__)
    logger.info(f"[MAIN] Named logger ({__name__}) ready. Service starting...")

    main_task = None
    try:
        # asyncio.run(main()) # Old call
        asyncio.run(main_wrapper()) # New call
    except KeyboardInterrupt:
        logger.info("⌨️ KeyboardInterrupt received by __main__. Attempting graceful shutdown...")
        if service.running: # If service was started
            logger.info("Stopping service due to KeyboardInterrupt...")
            # Need to run the async stop method
            try:
                asyncio.run(service.stop()) # Run the async stop method
            except RuntimeError as e:
                if "cannot be called when another loop is running" in str(e):
                    logger.warning(f"Could not run service.stop() due to loop conflict: {e}. Service might not have stopped cleanly.")
                else:
                    raise # Re-raise if it's a different RuntimeError
                
    finally:
        logger.info("🏁 Main execution finished.")
        # Ensure all handlers are flushed before exit
        for handler in logging.getLogger().handlers:
            handler.flush()