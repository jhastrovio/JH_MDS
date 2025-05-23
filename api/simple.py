"""Minimal API for testing Vercel deployment."""

from fastapi import FastAPI
from mangum import Mangum

# Create minimal app
app = FastAPI(title="Test API")

@app.get("/")
async def root():
    return {"message": "API is working", "status": "ok"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "Test API"}

# Vercel handler
handler = Mangum(app) 