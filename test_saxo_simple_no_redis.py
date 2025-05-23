"""Simple test of SaxoBank WebSocket connection without Redis dependency."""

import asyncio
import json
import os
from typing import Iterable
import websockets
import aiohttp

# Load environment variables from .env file
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

# Symbol to UIC mapping for common FX pairs
SYMBOL_TO_UIC = {
    "EUR-USD": 21,
    "GBP-USD": 22, 
    "USD-JPY": 23,
}

WS_URL = "wss://streaming.saxobank.com/openapi/streamingws/connect"
API_BASE = "https://gateway.saxobank.com/openapi"

async def create_subscription(symbol: str, context_id: str, token: str) -> str:
    """Create HTTP subscription for a symbol and return reference ID."""
    
    uic = SYMBOL_TO_UIC.get(symbol)
    if not uic:
        raise ValueError(f"Unknown symbol: {symbol}")
    
    reference_id = f"{symbol.replace('-', '_')}_sub"
    
    subscription_data = {
        "Arguments": {
            "AssetType": "FxSpot",
            "Uic": uic
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
        url = f"{API_BASE}/trade/v1/prices/subscriptions"
        print(f"🔗 Creating subscription for {symbol}...")
        async with session.post(url, json=subscription_data, headers=headers) as response:
            print(f"📡 Response status: {response.status}")
            response_text = await response.text()
            print(f"📡 Response: {response_text}")
            
            if response.status == 201:
                return reference_id
            else:
                raise RuntimeError(f"Subscription failed for {symbol}: {response.status} - {response_text}")

async def connect_websocket() -> websockets.WebSocketClientProtocol:
    """Open a WebSocket connection to the Saxo streaming endpoint."""
    
    token = os.environ.get("SAXO_API_TOKEN")
    if not token:
        raise RuntimeError("SAXO_API_TOKEN not set")
    
    context_id = "mds"
    url = f"{WS_URL}?contextId={context_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"🔗 Connecting to WebSocket: {url}")
    return await websockets.connect(url, additional_headers=headers)

async def test_saxo_connection():
    """Test the SaxoBank WebSocket connection and print received data."""
    
    # Load environment
    load_env()
    
    token = os.environ.get("SAXO_API_TOKEN")
    if not token:
        print("❌ SAXO_API_TOKEN not set in environment")
        return
    
    print(f"✅ Token loaded: {token[:20]}...")
    
    context_id = "mds"
    symbols = ["EUR-USD", "GBP-USD"]
    
    try:
        # Create subscriptions
        print(f"📡 Creating subscriptions for {len(symbols)} symbols...")
        reference_ids = []
        for symbol in symbols:
            try:
                ref_id = await create_subscription(symbol, context_id, token)
                reference_ids.append(ref_id)
                print(f"✅ Subscribed to {symbol} -> {ref_id}")
            except Exception as e:
                print(f"❌ Failed to subscribe to {symbol}: {e}")
        
        if not reference_ids:
            print("❌ No successful subscriptions created")
            return
        
        # Connect to WebSocket and receive data
        async with await connect_websocket() as ws:
            print(f"🔗 WebSocket connected, waiting for data...")
            
            # Read messages for a limited time
            message_count = 0
            async for raw in ws:
                try:
                    message_count += 1
                    print(f"📨 Message {message_count}: {len(raw)} bytes")
                    
                    # Parse the binary message format
                    if len(raw) < 16:
                        print("⚠️ Message too short, skipping...")
                        continue
                    
                    # Extract reference ID and payload
                    ref_id_size = raw[10]
                    if len(raw) < 11 + ref_id_size + 5:
                        print("⚠️ Invalid message format, skipping...")
                        continue
                    
                    ref_id = raw[11:11+ref_id_size].decode('ascii')
                    payload_size = int.from_bytes(raw[12+ref_id_size:16+ref_id_size], 'little')
                    
                    if len(raw) < 16 + ref_id_size + payload_size:
                        print("⚠️ Incomplete payload, skipping...")
                        continue
                    
                    payload = raw[16+ref_id_size:16+ref_id_size+payload_size]
                    data = json.loads(payload.decode('utf-8'))
                    
                    print(f"📊 Data for {ref_id}: {data}")
                    
                    # Extract quote data if present
                    if "Quote" in data:
                        quote = data["Quote"]
                        if "Ask" in quote and "Bid" in quote:
                            symbol = ref_id.replace("_sub", "").replace("_", "-")
                            print(f"💰 {symbol}: Bid={quote['Bid']}, Ask={quote['Ask']}")
                    
                    # Stop after 10 messages for testing
                    if message_count >= 10:
                        print("🛑 Stopping after 10 messages for testing")
                        break
                        
                except Exception as e:
                    print(f"❌ Error processing message: {e}")
                    continue
                    
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    asyncio.run(test_saxo_connection()) 