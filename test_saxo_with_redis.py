"""Test SaxoBank WebSocket streaming with Redis storage."""

import asyncio
import os
from pathlib import Path

def load_env():
    """Load environment variables from .env file."""
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

async def test_saxo_redis():
    """Test the full SaxoBank WebSocket to Redis pipeline."""
    
    # Load environment variables
    load_env()
    
    # Import after environment is loaded
    from ingest.saxo_ws import stream_quotes
    from storage.redis_client import get_redis
    
    print("🔗 Testing SaxoBank WebSocket with Redis storage...")
    print(f"✅ SAXO_API_TOKEN: {'SET' if os.environ.get('SAXO_API_TOKEN') else 'NOT SET'}")
    print(f"✅ REDIS_URL: {os.environ.get('REDIS_URL', 'NOT SET')}")
    
    # Test Redis connection first
    redis = get_redis()
    try:
        await redis.ping()
        print("✅ Redis connection: OK")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return
    
    # Test SaxoBank streaming (for a limited time)
    symbols = ['EUR-USD', 'GBP-USD', 'USD-JPY']
    print(f"📊 Starting stream for symbols: {symbols}")
    print("🕒 Will run for 30 seconds then stop...")
    
    try:
        # Run the streaming for 30 seconds
        streaming_task = asyncio.create_task(stream_quotes(symbols, redis))
        await asyncio.wait_for(streaming_task, timeout=30.0)
    except asyncio.TimeoutError:
        print("⏰ 30 seconds elapsed, stopping stream...")
        streaming_task.cancel()
        
        # Check what we got in Redis
        print("\n📊 Checking Redis for received data...")
        for symbol in symbols:
            key = f"fx:{symbol}"
            try:
                data = await redis.get(key)
                if data:
                    print(f"✅ {symbol}: {data}")
                else:
                    print(f"❌ {symbol}: No data found")
            except Exception as e:
                print(f"❌ {symbol}: Error reading from Redis: {e}")
                
    except Exception as e:
        print(f"❌ Streaming error: {e}")
    finally:
        await redis.close()
        print("🔒 Redis connection closed")

if __name__ == "__main__":
    asyncio.run(test_saxo_redis()) 