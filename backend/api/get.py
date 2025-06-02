import os
import sys
import json
from pathlib import Path

# Add the parent directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, Response
import redis.asyncio as redis

# Import from your settings
from core.settings import get_settings

settings = get_settings()
REDIS_URL = settings.REDIS_URL

app = FastAPI()

@app.api_route("/", methods=["GET"])
async def get_data_handler():
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
        print(f"[get] Error: {e}")
        if r.is_connected:
            await r.close()
        return Response(content=json.dumps({"error": "Data not available"}), status_code=503, media_type="application/json")

# Standard Vercel serverless handler
def handler(event, context):
    """
    Vercel serverless function handler for FastAPI app
    """
    # Print environment for debugging
    import os
    print("Environment Variables in get.py:")
    for key, value in os.environ.items():
        if key in ["REDIS_URL", "VERCEL"]:
            # Print only relevant variables and mask sensitive values
            masked_value = value[:5] + "..." if len(value) > 8 else "[masked]"
            print(f"{key}: {masked_value}")
            
    try:
        # Return the FastAPI app instance directly
        # Vercel will handle the ASGI adapter
        return app
    except Exception as e:
        print(f"Error in handler: {str(e)}")
        # Return a basic response in case of error
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)}),
            "headers": {"Content-Type": "application/json"}
        }
