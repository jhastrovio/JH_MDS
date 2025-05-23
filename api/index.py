from fastapi import FastAPI
from mangum import Mangum
from .router import router

app = FastAPI(title="JH Market Data API")
app.include_router(router)

# Vercel serverless handler
handler = Mangum(app) 