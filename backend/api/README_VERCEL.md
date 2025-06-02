# VERCEL PYTHON SERVERLESS DEPLOYMENT NOTES

This document explains how the FastAPI app is deployed to Vercel serverless functions.

## Vercel Function Structure

Each API endpoint in the `api/` folder follows this pattern:

```python
# Import necessary modules
import sys
from pathlib import Path

# Add parent directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import or define FastAPI app
from fastapi import FastAPI
app = FastAPI()

# Define routes...
@app.get("/")
async def root():
    return {"message": "Hello World"}

# Export handler for Vercel
def handler(event, context):
    # Return the FastAPI app directly
    return app
```

## Common Issues and Solutions

1. **`issubclass() arg 1 must be a class` error**
   - This happens when Vercel can't find a proper handler
   - Make sure the handler function returns the app instance directly

2. **Environment variables**
   - All env vars should be configured in Vercel dashboard
   - Required environment variables:
     - `REDIS_URL`: URL for Redis connection
     - `NEXT_PUBLIC_API_URL`: URL for the frontend app (used for CORS and API calls)
     - `JWT_SECRET`: Secret key for JWT token generation
   - Access environment variables via the settings module

3. **Dependencies**
   - Each API folder should have its own requirements.txt
   - Keep dependencies minimal for faster cold starts

## Debugging

- Check Vercel function logs in the Vercel dashboard
- Add print statements in your handler functions
- Test functions locally using the Vercel CLI:
  ```
  vercel dev
  ```

## Best Practices

1. Keep functions small and focused
2. Minimize dependencies for faster cold starts
3. Use Redis cache strategically for frequently accessed data
4. Set appropriate timeouts for external API calls
