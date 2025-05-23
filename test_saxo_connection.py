#!/usr/bin/env python3
"""Test script for SaxoBank WebSocket connection with real market data."""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from ingest.saxo_ws import stream_quotes
from storage.redis_client import get_redis

# Load environment variables from .env file
def load_env():
    env_path = ROOT_DIR / '.env'
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

# FX symbols to test
TEST_SYMBOLS = ['EUR-USD', 'GBP-USD', 'USD-JPY']

async def test_saxo_connection():
    """Test SaxoBank WebSocket connection and print incoming data."""
    
    load_env()
    
    print("🔧 Testing SaxoBank Market Data Connection...")
    print(f"📊 Symbols to test: {', '.join(TEST_SYMBOLS)}")
    print(f"🔑 API Token: {os.environ.get('SAXO_API_TOKEN', 'NOT SET')[:50]}...")
    print()
    
    # Check if token is set
    if not os.environ.get('SAXO_API_TOKEN') or os.environ.get('SAXO_API_TOKEN') == 'your-saxo-api-token-here':
        print("❌ SAXO_API_TOKEN not properly configured!")
        return
    
    # Create Redis connection
    redis = get_redis()
    
    try:
        print("🔗 Connecting to SaxoBank WebSocket...")
        
        # This will run indefinitely, streaming real data
        await stream_quotes(TEST_SYMBOLS, redis)
        
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Check your SAXO_API_TOKEN is valid")
        print("   2. Ensure you have internet connection")
        print("   3. Verify the token hasn't expired (24hr limit)")
    finally:
        await redis.close()
        print("✅ Cleanup complete")

if __name__ == "__main__":
    asyncio.run(test_saxo_connection()) 