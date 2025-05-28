import sys
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path('backend')))
from storage.redis_client import get_redis

async def test_redis():
    """Test Redis connectivity and populate with test data."""
    print("🔗 Connecting to Redis...")
    redis = get_redis()
    
    try:
        # Test data
        test_data = {
            "EUR-USD": {
                "symbol": "EUR-USD",
                "bid": 1.08745,
                "ask": 1.08755,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            "GBP-USD": {
                "symbol": "GBP-USD", 
                "bid": 1.26432,
                "ask": 1.26442,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        
        # Store test data
        for symbol, data in test_data.items():
            key = f"fx:{symbol}"
            serialized = json.dumps(data)
            await redis.set(key, serialized, ex=300)  # 5 minute expiry
            print(f"✅ Stored {symbol}: {data['bid']}/{data['ask']}")
            
        print("🎉 Test data populated successfully!")
        print("📊 EUR-USD and GBP-USD should now show real data in frontend")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await redis.aclose()

def print_status():
    async def check_status():
        redis = get_redis()
        try:
            status = await redis.get('service:market_data:status')
            heartbeat = await redis.get('service:market_data:heartbeat')
            print(f'Final status: {status}')
            print(f'Last heartbeat: {heartbeat}')
        finally:
            await redis.aclose()
    asyncio.run(check_status())

async def check_live_data():
    redis = get_redis()
    try:
        for symbol in ["EUR-USD", "GBP-USD"]:
            val = await redis.get(f"fx:{symbol}")
            if val:
                data = json.loads(val)
                print(f"🔎 {symbol} from Redis: {data}")
            else:
                print(f"⚠️  No data found in Redis for {symbol}")
    finally:
        await redis.aclose()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "status":
        print_status()
    elif len(sys.argv) > 1 and sys.argv[1] == "live":
        asyncio.run(check_live_data())
    else:
        asyncio.run(test_redis())