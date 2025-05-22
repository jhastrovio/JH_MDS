from fastapi import FastAPI

from api import router as api_router

app = FastAPI(title="JH Market Data API")
app.include_router(api_router, prefix="/api")
