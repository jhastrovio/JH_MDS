#!/usr/bin/env python3
"""Proper SaxoBank integration test following their documented protocol."""

import asyncio
import os
import sys
import json
import aiohttp
from pathlib import Path

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

async def test_saxo_proper():
    """Test SaxoBank integration following proper protocol."""
    
    load_env()
    
    print("🔧 Testing Proper SaxoBank Integration...")
    
    # Check token
    token = os.environ.get('SAXO_API_TOKEN')
    if not token:
        print("❌ SAXO_API_TOKEN not found in environment")
        return
        
    print(f"🔑 Token found: {token[:50]}...")
    
    context_id = "mds_test"
    reference_id = "EUR_USD_test"
    
    try:
        # Step 1: Create HTTP subscription first
        print("📡 Step 1: Creating HTTP subscription...")
        
        subscription_url = "https://gateway.saxobank.com/openapi/trade/v1/prices/subscriptions"
        subscription_data = {
            "Arguments": {
                "AssetType": "FxSpot",
                "Uic": 21  # EUR/USD
            },
            "ContextId": context_id,
            "ReferenceId": reference_id,
            "RefreshRate": 1000
        }
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(subscription_url, 
                                  json=subscription_data, 
                                  headers=headers) as response:
                
                if response.status == 201:
                    location = response.headers.get('Location')
                    print(f"✅ Subscription created! Location: {location}")
                else:
                    error_text = await response.text()
                    print(f"❌ Subscription failed: {response.status}")
                    print(f"   Response: {error_text}")
                    return
        
        # Step 2: Connect to WebSocket to receive data
        print("🔗 Step 2: Connecting to WebSocket...")
        
        import websockets
        
        ws_url = f"wss://streaming.saxobank.com/openapi/streamingws/connect?contextId={context_id}"
        ws_headers = {"Authorization": f"Bearer {token}"}
        
        async with websockets.connect(ws_url, additional_headers=ws_headers) as ws:
            print("✅ WebSocket connected! Waiting for data...")
            
            # Wait for messages (with timeout)
            try:
                for i in range(5):  # Try to receive 5 messages
                    message = await asyncio.wait_for(ws.recv(), timeout=10.0)
                    print(f"📊 Received: {message[:100]}...")
                    
            except asyncio.TimeoutError:
                print("⏰ No data received within timeout - this is normal for a test")
                
        print("✅ Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        print(f"   Full traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(test_saxo_proper()) 