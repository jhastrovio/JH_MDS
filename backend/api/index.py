# api/index.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.auth.router import router as auth_router

app = FastAPI(title="JH Market Data API")

# CORS Configuration
origins = [
    "https://jh-mds-frontend.vercel.app", # Your frontend URL
    # You can add other origins here if needed, e.g., for local development
    # "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allows all standard methods
    allow_headers=["*"], # Allows all standard headers
)

print("👋 index.py loaded – CORS configured, mounting routes…")
# Mount your auth router under /api
# The prefix here means routes in auth_router like /status will be at /api/auth/status
app.include_router(auth_router, prefix="/api")



