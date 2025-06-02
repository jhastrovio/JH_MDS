import os
import time
import json
import httpx
import redis.asyncio as redis
from fastapi import FastAPI, Response

EXTERNAL_API_URL = os.getenv("EXTERNAL_API_URL")
REDIS_URL = os.getenv("REDIS_URL")

app = FastAPI()

@app.api_route("/", methods=["GET", "POST"])
async def handler():
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
    return Response(content=json.dumps({"status": status, "timestamp": now}), media_type="application/json")
