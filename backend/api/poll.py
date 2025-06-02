import os
import time
import json
import httpx
import sys
from pathlib import Path

# Add the parent directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, Response
import redis.asyncio as redis

# Import from your settings
from core.settings import get_settings

settings = get_settings()
EXTERNAL_API_URL = settings.EXTERNAL_API_URL
REDIS_URL = settings.REDIS_URL

app = FastAPI()

@app.api_route("/", methods=["GET", "POST"])
async def poll_handler():
    status = "ok"
    now = int(time.time() * 1000)
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(EXTERNAL_API_URL, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        r = redis.from_url(REDIS_URL, decode_responses=True)
        await r.set("latest_data", json.dumps(data), ex=60)
        await r.close()
    except Exception as e:
        print(f"[poll] Error: {e}")
        status = "error"
    return Response(content=json.dumps({"status": status, "timestamp": now}), media_type="application/json")

# Standard Vercel serverless handler
def handler(event, context):
    """
    Vercel serverless function handler for FastAPI app
    """
    # Return the FastAPI app instance directly
    # Vercel will handle the ASGI adapter
    return app
