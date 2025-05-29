import asyncio
import os
import sys
from pathlib import Path

# Add backend directory to path for imports
BACKEND_DIR = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from ingest.saxo_ws import stream_quotes
from storage.redis_client import get_redis

# FX symbols to stream
FX_SYMBOLS = [
    'EUR-USD', 'GBP-USD', 'USD-JPY', 'AUD-USD', 
    'USD-CHF', 'USD-CAD', 'NZD-USD'
]

async def main():
    print("ðŸ”— Connecting to SaxoBank WebSocket...")
    print(f"ðŸ“Š Streaming symbols: {', '.join(FX_SYMBOLS)}")
    
    redis = get_redis()
    try:
        await stream_quotes(FX_SYMBOLS, redis)
    except Exception as e:
        print(f"âŒ Error: {e}")
        print("ðŸ'¡ Check your SAXO_API_TOKEN in .env")
    finally:
        await redis.close()

if __name__ == "__main__":
    asyncio.run(main())
