# backend/routers/auth.py

from fastapi import APIRouter, Depends, HTTPException
from core.deps import get_settings, get_logger, get_redis
from services.oauth_client import parse_token_response, SaxoOAuthClient
from redis.asyncio import Redis

router = APIRouter(prefix="/auth", tags=["auth"])

@router.get("/login")
async def login(
    settings=Depends(get_settings),
    logger=Depends(get_logger),
):
    # Redirect user to Saxo OAuth login
    return {
        "url": SaxoOAuthClient(settings, logger).login_url()
    }

@router.get("/callback")
async def callback(
    code: str,
    settings=Depends(get_settings),
    redis=Depends(get_redis),
    logger=Depends(get_logger),
):
    # Exchange code for token, store in Redis
    raw = await SaxoOAuthClient(settings, logger).exchange_code(code)
    token = parse_token_response(raw)
    await redis.set("saxo_token", token.json())
    return {"access_token": token.access_token}
