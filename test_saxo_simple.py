#!/usr/bin/env python3
"""Simple SaxoBank connection test with timeout."""

import asyncio
import os
import sys
from pathlib import Path
import json

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

def load_env():
    """Load environment variables from .env file."""
    env_path = ROOT_DIR / '.env'
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

async def test_saxo_simple():
    """Test SaxoBank connection with timeout."""
    
    load_env()
    
    print("🔧 Simple SaxoBank Connection Test...")
    
    # Check token
    token = os.environ.get('SAXO_API_TOKEN')
    if not token:
        print("❌ SAXO_API_TOKEN not found in environment")
        return
    
    if token == 'your-saxo-api-token-here':
        print("❌ SAXO_API_TOKEN is still the placeholder value")
        return
        
    print(f"🔑 Token found: {token[:50]}...")
    
    # Try connection with timeout
    try:
        import websockets
        
        # Create contextId and use proper authentication
        context_id = "test_connection_123"
        url = f"wss://streaming.saxobank.com/openapi/streamingws/connect?contextId={context_id}"
        print(f"🔗 Connecting to: {url}")
        
        # Add timeout to prevent hanging - use proper headers
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        ws = await asyncio.wait_for(
            websockets.connect(url, additional_headers=headers),
            timeout=10.0
        )
        
        print("✅ WebSocket connection established!")
        
        # Try sending a subscription message
        message = {
            "ContextId": "test",
            "Instruments": ["EUR-USD"]
        }
        
        await ws.send(json.dumps(message))
        print("✅ Subscription message sent")
        
        # Try receiving a message with timeout
        response = await asyncio.wait_for(ws.recv(), timeout=5.0)
        print(f"✅ Received response: {response[:100]}...")
        
        await ws.close()
        print("✅ Connection closed cleanly")
        
    except asyncio.TimeoutError:
        print("⏰ Connection timed out - this suggests:")
        print("   1. Network/firewall blocking WebSocket connections")
        print("   2. SaxoBank API endpoint may be down")
        print("   3. Token may be expired or invalid")
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        print(f"   Full traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(test_saxo_simple()) 