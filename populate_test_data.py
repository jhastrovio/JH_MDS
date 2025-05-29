#!/usr/bin/env python3
"""Populate Redis with test market data."""

import asyncio
import json
from datetime import datetime
from backend.storage.redis_client import get_redis

async def populate_test_data():
    """Add sample market data to Redis for testing."""
    redis = get_redis()
    
    # Sample FX data
    test_data = {
        "EURUSD": {"symbol": "EURUSD", "bid": 1.0845, "ask": 1.0847, "timestamp": datetime.now().isoformat()},
        "GBPUSD": {"symbol": "GBPUSD", "bid": 1.2654, "ask": 1.2656, "timestamp": datetime.now().isoformat()},
        "USDJPY": {"symbol": "USDJPY", "bid": 157.45, "ask": 157.47, "timestamp": datetime.now().isoformat()},
        "AUDUSD": {"symbol": "AUDUSD", "bid": 0.6598, "ask": 0.6600, "timestamp": datetime.now().isoformat()},
        "USDCAD": {"symbol": "USDCAD", "bid": 1.3756, "ask": 1.3758, "timestamp": datetime.now().isoformat()},
    }
    
    try:
        for symbol, data in test_data.items():
            key = f"fx:{symbol}"
            await redis.set(key, json.dumps(data))
            print(f"Added test data for {symbol}")
        
        print(f"Successfully populated {len(test_data)} test symbols")
        
    except Exception as e:
        print(f"Error populating test data: {e}")
    finally:
        await redis.close()

if __name__ == "__main__":
    asyncio.run(populate_test_data())
