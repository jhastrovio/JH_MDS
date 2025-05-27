# api/index.py
from fastapi import FastAPI
from app.auth.router import router as auth_router

app = FastAPI(title="JH Market Data API")

print("👋 index.py loaded – mounting routes…")
# Mount your auth router under /api/auth
app.include_router(auth_router, prefix="/api")



