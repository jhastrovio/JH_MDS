# api/index.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.auth.router import router as auth_router

app = FastAPI(title="JH Market Data API")

# CORS Configuration for Vercel deployment
def get_cors_origins():
    """Get CORS origins based on environment."""
    # Default origins for production
    origins = [
        "https://jh-mds-frontend.vercel.app",  # Your main frontend URL
    ]
    
    # Add environment-specific origins
    if os.environ.get("VERCEL"):
        # On Vercel, allow common Vercel domain patterns
        origins.extend([
            "https://*.vercel.app",  # All Vercel preview deployments
            "https://jh-mds-frontend-*.vercel.app",  # Branch deployments
        ])
    else:
        # Local development
        origins.extend([
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ])
    
    # Allow custom frontend URL from environment
    custom_frontend = os.environ.get("FRONTEND_URL")
    if custom_frontend:
        origins.append(custom_frontend)
    
    return origins

origins = get_cors_origins()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allows all standard methods
    allow_headers=["*"], # Allows all standard headers
)

print(f"👋 index.py loaded – CORS configured for origins: {origins}")
print(f"🌍 Environment: {'Vercel' if os.environ.get('VERCEL') else 'Local'}")

# Mount your auth router under /api
# The prefix here means routes in auth_router like /status will be at /api/auth/status
app.include_router(auth_router, prefix="/api")



