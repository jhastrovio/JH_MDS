import sys
import os
from pathlib import Path

# Add the project root to Python path for imports
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from fastapi import FastAPI
    from mangum import Mangum
    
    # Import the router with absolute path
    from api.router import router
    
    app = FastAPI(title="JH Market Data API")
    app.include_router(router)
    
    # Add a root endpoint for testing
    @app.get("/")
    async def root():
        return {"message": "JH Market Data API is running", "status": "ok"}
    
    # Vercel serverless handler
    handler = Mangum(app)
    
except Exception as e:
    # Fallback handler if imports fail
    def handler(event, context):
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": f'{{"error": "API setup failed", "detail": "{str(e)}"}}'
        } 