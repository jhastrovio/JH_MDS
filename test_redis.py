import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add backend directory to path for imports
BACKEND_DIR = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

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

if __name__ == "__main__":
    asyncio.run(test_redis()) 