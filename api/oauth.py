"""OAuth implementation for SaxoBank Live API authentication."""

from __future__ import annotations

import os
import secrets
from typing import Dict, Optional
from datetime import datetime, timedelta
from fastapi import HTTPException
from pydantic import BaseModel
import json

try:
    import aiohttp
except ImportError:
    aiohttp = None

# OAuth Configuration
SAXO_AUTH_URL = "https://live.logonvalidation.net/authorize"
SAXO_TOKEN_URL = "https://live.logonvalidation.net/token"

class OAuthConfig(BaseModel):
    """OAuth configuration from environment variables."""
    client_id: str
    client_secret: str
    redirect_uri: str
    
    @classmethod
    def from_env(cls) -> "OAuthConfig":
        """Create OAuth config from environment variables."""
        client_id = os.environ.get("SAXO_APP_KEY")
        client_secret = os.environ.get("SAXO_APP_SECRET") 
        redirect_uri = os.environ.get("SAXO_REDIRECT_URI")
        
        if not all([client_id, client_secret, redirect_uri]):
            raise HTTPException(
                status_code=500, 
                detail="Missing OAuth configuration: SAXO_APP_KEY, SAXO_APP_SECRET, SAXO_REDIRECT_URI"
            )
        
        return cls(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri
        )

class SaxoToken(BaseModel):
    """SaxoBank OAuth token model."""
    access_token: str
    refresh_token: str
    expires_at: datetime
    token_type: str = "Bearer"
    
    @property
    def is_expired(self) -> bool:
        """Check if token is expired (with 5 min buffer)."""
        return datetime.now() >= (self.expires_at - timedelta(minutes=5))

class SaxoOAuth:
    """SaxoBank OAuth client."""
    
    def __init__(self):
        self.config = OAuthConfig.from_env()
        self._current_token: Optional[SaxoToken] = None
        self._state_store: Dict[str, str] = {}
    
    def get_authorization_url(self) -> tuple[str, str]:
        """Generate authorization URL and state for OAuth flow."""
        state = secrets.token_urlsafe(32)
        
        params = {
            "response_type": "code",
            "client_id": self.config.client_id,
            "redirect_uri": self.config.redirect_uri,
            "state": state,
            "scope": "openapi"  # SaxoBank scope for market data
        }
        
        param_string = "&".join([f"{k}={v}" for k, v in params.items()])
        auth_url = f"{SAXO_AUTH_URL}?{param_string}"
        
        # Store state for validation
        self._state_store[state] = "pending"
        
        return auth_url, state
    
    async def exchange_code_for_token(self, code: str, state: str) -> SaxoToken:
        """Exchange authorization code for access token."""
        if aiohttp is None:
            raise HTTPException(status_code=500, detail="aiohttp not available for OAuth")
            
        # Validate state
        if state not in self._state_store:
            raise HTTPException(status_code=400, detail="Invalid state parameter")
        
        # Prepare token request
        token_data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.config.redirect_uri,
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                SAXO_TOKEN_URL, 
                data=token_data, 
                headers=headers
            ) as response:
                response_text = await response.text()
                try:
                    token_response = json.loads(response_text)
                except json.JSONDecodeError:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid token response: {response_text}"
                    )
                
                if response.status != 200:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Token exchange failed: {response_text}"
                    )
                
                if "access_token" not in token_response:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Missing access_token in response: {response_text}"
                    )
        
        # Create token object
        expires_in = token_response.get("expires_in", 3600)  # Default 1 hour
        expires_at = datetime.now() + timedelta(seconds=expires_in)
        
        token = SaxoToken(
            access_token=token_response["access_token"],
            refresh_token=token_response.get("refresh_token", ""),
            expires_at=expires_at,
            token_type=token_response.get("token_type", "Bearer")
        )
        
        # Store current token
        self._current_token = token
        
        # Clean up state
        del self._state_store[state]
        
        return token
    
    async def refresh_token(self, refresh_token: str) -> SaxoToken:
        """Refresh access token using refresh token."""
        if aiohttp is None:
            raise HTTPException(status_code=500, detail="aiohttp not available for token refresh")
            
        token_data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                SAXO_TOKEN_URL,
                data=token_data,
                headers=headers
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    raise HTTPException(
                        status_code=400,
                        detail=f"Token refresh failed: {error_text}"
                    )
                
                token_response = await response.json()
        
        # Create new token object
        expires_in = token_response.get("expires_in", 3600)
        expires_at = datetime.now() + timedelta(seconds=expires_in)
        
        token = SaxoToken(
            access_token=token_response["access_token"],
            refresh_token=token_response.get("refresh_token", refresh_token),  # Keep old if not provided
            expires_at=expires_at,
            token_type=token_response.get("token_type", "Bearer")
        )
        
        self._current_token = token
        return token
    
    async def get_valid_token(self) -> str:
        """Get a valid access token, refreshing if necessary."""
        if not self._current_token:
            raise HTTPException(
                status_code=401, 
                detail="No token available. Please authenticate first."
            )
        
        if self._current_token.is_expired:
            if not self._current_token.refresh_token:
                raise HTTPException(
                    status_code=401,
                    detail="Token expired and no refresh token available"
                )
            
            # Refresh the token
            await self.refresh_token(self._current_token.refresh_token)
        
        return self._current_token.access_token

# Global OAuth client instance
try:
    oauth_client = SaxoOAuth()
except Exception:
    # If OAuth setup fails (missing env vars), create a dummy client
    oauth_client = None 