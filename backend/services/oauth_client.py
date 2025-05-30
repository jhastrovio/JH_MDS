# backend/core/oauth_client.py
"""SaxoBank OAuth client logic, fully DI-powered and testable."""

import secrets
import json
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple

from fastapi import Depends, HTTPException
from httpx import AsyncClient
from pydantic import BaseModel

from core.settings import Settings
from core.deps import get_logger, get_redis, get_httpx_client, get_settings


# OAuth endpoints
SAXO_AUTH_URL = "https://live.logonvalidation.net/authorize"
SAXO_TOKEN_URL = "https://live.logonvalidation.net/token"


class SaxoToken(BaseModel):
    access_token: str
    refresh_token: str
    expires_at: datetime
    token_type: str = "Bearer"

    @property
    def is_expired(self) -> bool:
        """Check if token is expired (5-minute buffer)."""
        return datetime.utcnow() >= (self.expires_at - timedelta(minutes=5))


def parse_token_response(raw: Dict[str, Any]) -> SaxoToken:
    """
    Validate Saxo token JSON; raise HTTPException on error.
    """
    if error := raw.get("error"):
        detail = raw.get("error_description") or error
        raise HTTPException(status_code=400, detail=f"Saxo OAuth error: {detail}")
    try:
        expires_in = int(raw["expires_in"])
        return SaxoToken(
            access_token=raw["access_token"],
            refresh_token=raw["refresh_token"],
            expires_at=datetime.utcnow() + timedelta(seconds=expires_in),
            token_type=raw.get("token_type", "Bearer"),
        )
    except KeyError as e:
        raise HTTPException(status_code=500, detail=f"Missing field in token response: {e}")


class SaxoOAuthClient:
    """
    SaxoBank OAuth client, instantiated with DI for settings, logging,
    HTTP client, and Redis.
    """

    def __init__(
        self,
        settings: Settings = Depends(get_settings),
        logger = Depends(get_logger),
        client: AsyncClient = Depends(get_httpx_client),
        redis = Depends(get_redis),
    ):
        self.settings = settings
        self.logger = logger
        self.client = client
        self.redis = redis

    async def get_authorization_url(self) -> Tuple[str, str]:
        """
        Generate the OAuth authorization URL and a one-time state token
        (stored in Redis for 10 minutes).
        """
        state = secrets.token_urlsafe(32)
        await self.redis.set(f"oauth:state:{state}", "pending", ex=600)

        params = {
            "response_type": "code",
            "client_id": self.settings.SAXO_APP_KEY,
            "redirect_uri": self.settings.SAXO_REDIRECT_URI,
            "state": state,
            "scope": "openapi",
        }
        query = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{SAXO_AUTH_URL}?{query}"
        return url, state

    async def exchange_code_for_token(self, code: str, state: str) -> SaxoToken:
        """
        Exchange the authorization code for an access token.
        Validates and removes the state from Redis, then parses and stores token.
        """
        # Validate state
        if not await self.redis.get(f"oauth:state:{state}"):
            raise HTTPException(status_code=400, detail="Invalid OAuth state")
        await self.redis.delete(f"oauth:state:{state}")

        # Request token
        resp = await self.client.post(
            SAXO_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self.settings.SAXO_REDIRECT_URI,
                "client_id": self.settings.SAXO_APP_KEY,
                "client_secret": self.settings.SAXO_SECRET,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        raw = resp.json()
        token = parse_token_response(raw)

        # Persist token in Redis (with 5-minute buffer)
        ttl = int((token.expires_at - datetime.utcnow()).total_seconds()) + 300
        await self.redis.set("saxo:current_token", token.json(), ex=ttl)

        return token

    async def refresh_token(self, refresh_token: str) -> SaxoToken:
        """
        Refresh the access token using a refresh token.
        """
        resp = await self.client.post(
            SAXO_TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": self.settings.SAXO_APP_KEY,
                "client_secret": self.settings.SAXO_SECRET,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        raw = resp.json()
        token = parse_token_response(raw)

        ttl = int((token.expires_at - datetime.utcnow()).total_seconds()) + 300
        await self.redis.set("saxo:current_token", token.json(), ex=ttl)
        return token

    async def get_valid_token(self) -> str:
        """
        Retrieve a non-expired access token, refreshing it if necessary.
        """
        stored = await self.redis.get("saxo:current_token")
        if stored:
            try:
                token = SaxoToken.parse_raw(stored)
            except Exception as e:
                self.logger.error("Corrupted token data in Redis: %s", e)
                await self.redis.delete("saxo:current_token")
                raise HTTPException(status_code=500, detail="Corrupted token data")
            if not token.is_expired:
                return token.access_token
            # Refresh expired token
            token = await self.refresh_token(token.refresh_token)
            return token.access_token

        raise HTTPException(status_code=401, detail="No token found; please authenticate first.")
