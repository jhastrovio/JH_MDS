# backend/api/index.py

import sys
import os
from pathlib import Path

# Add the parent directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import app

# Standard Vercel serverless handler
def handler(event, context):
    """
    Vercel serverless function handler for FastAPI app
    """
    # Print environment for debugging
    import os
    import json
    
    print("Environment Variables in index.py:")
    for key, value in os.environ.items():
        if key in ["REDIS_URL", "NEXT_PUBLIC_API_URL", "VERCEL"]:
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
