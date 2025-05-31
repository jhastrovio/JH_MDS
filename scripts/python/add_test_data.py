#!/usr/bin/env python3
"""Add test data to Redis for testing the market endpoint."""

import asyncio
import json
import os
from datetime import datetime
import redis
from dotenv import load_dotenv

async def add_test_data():
    """Add sample market data to Redis."""
    # Load the .env file
    load_dotenv()
    redis_url = os.getenv("REDIS_URL")
    
    r = redis.from_url(redis_url, decode_responses=True)
    
    # Test data with the format from market_data.py
    symbols = ["EUR-USD", "GBP-USD", "USD-JPY", "AUD-USD", "USD-CHF", "USD-CAD", "NZD-USD"]
    
    for symbol in symbols:
        test_data = {
            "symbol": symbol,
            "bid": 1.2345,
            "ask": 1.2347,
            "timestamp": datetime.now().isoformat()
        }
        
        # Set the latest price
        key = f"fx:{symbol}"
        r.set(key, json.dumps(test_data))
        print(f"Added test data for {symbol}")
          # Add some tick history
        tick_key = f"ticks:{symbol}"
        for i in range(5):
            tick = {
                "symbol": symbol,
                "bid": 1.2345 + (i * 0.0001),
                "ask": 1.2347 + (i * 0.0001),
                "timestamp": datetime.now().isoformat()
            }
            # The API expects json.dumps(tick), but as a string that can be passed to parse_raw
            r.lpush(tick_key, json.dumps(json.dumps(tick)))
        print(f"Added 5 historical ticks for {symbol}")
    
    print(f"Successfully populated {len(symbols)} test symbols")
    r.close()

if __name__ == "__main__":
    asyncio.run(add_test_data())
