# api/app.py

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from redis.asyncio import Redis
import httpx
import logging
import os
import json

from core.settings import get_settings
from routers.auth import router as auth_router
from routers.market import router as market_router
from routers.health import router as health_router
from routers.diagnostics import router as diagnostics_router
from core.security import get_security_headers


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="JH Market Data API",
        version="1.0.0",
        description="Real-time market data API with SaxoBank integration",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )

    # === CORS ===
    origins = settings.get_cors_origins()
    logging.getLogger("jh").info(f"CORS origins: {origins}")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # === Security headers middleware ===
    @app.middleware("http")
    async def apply_security_headers(request, call_next):
        response = await call_next(request)
        response.headers.update(get_security_headers(settings))
        return response

    # === Routers ===
    app.include_router(auth_router)
    app.include_router(market_router)
    app.include_router(health_router)
    if settings.ENV != "production":
        app.include_router(diagnostics_router)

    # === Redis and settings in app.state ===
    app.state.redis = Redis.from_url(
        str(settings.REDIS_URL),
        max_connections=settings.REDIS_POOL_SIZE
    )
    app.state.settings = settings

    # === SessionMiddleware ===
    app.add_middleware(SessionMiddleware, secret_key=settings.JWT_SECRET)
    logging.getLogger("jh").info(f"SAXO_APP_SECRET loaded: {settings.SAXO_APP_SECRET!r}")
    logging.getLogger("jh").info(f"ALL ENV VARS: {os.environ}")

    # === New: /api/poll endpoint ===    @app.get("/api/poll")
    async def poll_handler():
        """
        One‐shot polling:
        1. Fetch JSON from external URL (prioritizing NEXT_PUBLIC_API_URL).
        2. Write it into Redis under "latest_data" with EX=60.
        3. Return 200 (even on fetch/Redis error) so Cron keeps running.
        """
        settings = app.state.settings
        
        # Get API URL - prefer NEXT_PUBLIC_API_URL since that's what's configured in Vercel
        api_url = settings.NEXT_PUBLIC_API_URL
        if not api_url:
            # Fall back to other possible sources
            api_url = settings.EXTERNAL_API_URL or os.getenv("NEXT_PUBLIC_API_URL") or "https://api.example.com/data"
            
        logging.getLogger("jh").info(f"Using API URL: {api_url}")
        api_endpoint = api_url
        redis: Redis = app.state.redis# 1) Fetch from external API
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(api_endpoint)
                resp.raise_for_status()
                data = resp.json()
        except Exception as fetch_err:
            logging.getLogger("jh").error(f"[poll] fetch error: {fetch_err}")
            # Return 200 so Cron stays enabled
            return Response(
                content=json.dumps({"status": "fetch_error", "error": str(fetch_err)}),
                media_type="application/json",
                status_code=200
            )

        # 2) Write to Redis with TTL=60
        try:
            # Note: using same Redis instance in app.state
            await redis.set("latest_data", json.dumps(data), ex=60)
        except Exception as redis_err:
            logging.getLogger("jh").error(f"[poll] redis error: {redis_err}")
            return Response(
                content=json.dumps({"status": "redis_error", "error": str(redis_err)}),
                media_type="application/json",
                status_code=200
            )

        # 3) Success
        return {"status": "ok", "timestamp": int(__import__("time").time() * 1000)}

    # === New: /api/get endpoint ===
    @app.get("/api/get")
    async def get_handler():
        """
        Return whatever is in Redis under "latest_data". If not present, 503.
        """
        redis: Redis = app.state.redis
        try:
            raw = await redis.get("latest_data")
        except Exception as e:
            logging.getLogger("jh").error(f"[get] redis/read error: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

        if raw is None:
            # No data available (either first run or TTL expired)
            raise HTTPException(status_code=503, detail="Data not available")

        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            logging.getLogger("jh").error(f"[get] JSON decode error: {e}")
            raise HTTPException(status_code=500, detail="Corrupt data")

    return app


# Instantiate the FastAPI app
app = create_app()
