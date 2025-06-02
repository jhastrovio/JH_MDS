import os
import json
from fastapi import Response
import redis.asyncio as redis

REDIS_URL = os.getenv("REDIS_URL")

async def handler(request):
    r = redis.from_url(REDIS_URL, decode_responses=True)
    try:
        val = await r.get("latest_data")
        if val is None:
            await r.close()
            return Response(content=json.dumps({"error": "Data not available"}), status_code=503, media_type="application/json")
        data = json.loads(val)
        await r.close()
        return Response(content=json.dumps(data), media_type="application/json")
    except Exception as e:
        await r.close()
        return Response(content=json.dumps({"error": "Data not available"}), status_code=503, media_type="application/json")
