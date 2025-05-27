from fastapi import FastAPI
from app.auth.router import router as auth_router

app = FastAPI(title="JH Market Data API")

# now all routes in auth_router (e.g. "/price", "/auth/login", etc.)
# will live at "/api/price", "/api/auth/login", etc.
app.include_router(auth_router, prefix="/api")

import logging

for route in app.router.routes:
    logging.error(f"📌 Route registered: {route.name} → {route.path}")
