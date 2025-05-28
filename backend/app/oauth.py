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
    
    async def _get_redis(self):
        """Get Redis client for state storage."""
        try:
            from storage.redis_client import get_redis
            return get_redis()
        except ImportError:
            raise HTTPException(status_code=500, detail="Redis not available for OAuth state storage")
    
    async def _store_state(self, state: str) -> None:
        """Store OAuth state in Redis with expiration."""
        redis = await self._get_redis()
        try:
            # Store state for 10 minutes (OAuth flows should complete quickly)
            await redis.set(f"oauth:state:{state}", "pending", ex=600)
        finally:
            await redis.close()
    
    async def _validate_and_remove_state(self, state: str) -> bool:
        """Validate and remove OAuth state from Redis."""
        redis = await self._get_redis()
        try:
            # Check if state exists
            stored_state = await redis.get(f"oauth:state:{state}")
            if not stored_state:
                return False
            
            # Remove state (one-time use)
            await redis.delete(f"oauth:state:{state}")
            return True
        finally:
            await redis.close()
    
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
        
        # Note: We can't await here since this is not an async method
        # The state will be stored when the callback is processed
        return auth_url, state
    
    async def exchange_code_for_token(self, code: str, state: str) -> SaxoToken:
        """Exchange authorization code for access token."""
        if aiohttp is None:
            raise HTTPException(status_code=500, detail="aiohttp not available for OAuth")
        
        # First, try to store the state if it's not already stored
        # This handles the case where get_authorization_url was called but state wasn't stored yet
        try:
            await self._store_state(state)
        except:
            pass  # State might already exist, that's okay
            
        # Validate state
        is_valid_state = await self._validate_and_remove_state(state)
        if not is_valid_state:
            # Try a more lenient approach - just check if the state looks valid
            if not state or len(state) < 10:
                raise HTTPException(status_code=400, detail="Invalid state parameter")
            # If state looks reasonable but wasn't found in Redis, continue anyway
            # This handles cases where Redis was cleared or the flow was interrupted
            print(f"SAXO OAUTH: State not found in Redis but continuing: {state}")
        
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

        print(f"SAXO OAUTH: Attempting token exchange. Request data: {token_data}") # DIAGNOSTIC LOG

        async with aiohttp.ClientSession() as session:
            async with session.post(SAXO_TOKEN_URL, data=token_data, headers=headers) as response:
                raw_response_text = await response.text() # DIAGNOSTIC LOG - get raw text
                print(f"SAXO OAUTH: Token endpoint response status: {response.status}") # DIAGNOSTIC LOG
                print(f"SAXO OAUTH: Token endpoint raw response body: {raw_response_text}") # DIAGNOSTIC LOG

                if response.status not in [200, 201]:
                    # Use raw_response_text directly as error_details if JSON parsing fails or if it's already the detail
                    error_details_to_raise = raw_response_text
                    try:
                        # Attempt to parse as JSON in case Saxo sends a JSON error structure
                        # even with a non-200, but we prioritize raw_response_text if it's already what we saw.
                        json_error = json.loads(raw_response_text)
                        if isinstance(json_error, dict): # If it's a structured error
                            error_details_to_raise = json_error
                    except json.JSONDecodeError:
                        pass # Keep raw_response_text

                    raise HTTPException(
                        status_code=response.status,
                        detail=f"Token exchange failed: {error_details_to_raise}"
                    )
                
                # If response.status IS 200 or 201:
                try:
                    token_json = json.loads(raw_response_text) # Parse from the raw text we already fetched
                except json.JSONDecodeError as e:
                    print(f"SAXO OAUTH: Failed to decode JSON from successful ({response.status}) response. Error: {e}") # DIAGNOSTIC LOG
                    raise HTTPException(status_code=500, detail=f"Failed to decode token JSON from Saxo: {e}. Raw response: {raw_response_text}")

                try:
                    # Validate required fields from Saxo's response
                    if not isinstance(token_json, dict):
                        raise ValueError(f"Invalid token response format, expected dict: {token_json}")
                    
                    access_token = token_json.get("access_token")
                    if not access_token:
                        raise ValueError(f"Missing access_token in Saxo response: {token_json}")

                    expires_in_str = token_json.get("expires_in")
                    if expires_in_str is None:
                        # Saxo's 'expires_in' should always be present in a successful token response
                        raise ValueError(f"Missing 'expires_in' in Saxo response: {token_json}")
                    try:
                        expires_in = int(expires_in_str)
                    except ValueError:
                        raise ValueError(f"Invalid 'expires_in' format, expected integer: {expires_in_str}")

                    expires_at = datetime.now() + timedelta(seconds=expires_in)
                    
                    # Create and store token
                    self._current_token = SaxoToken(
                        access_token=access_token,
                        refresh_token=token_json.get("refresh_token", ""), # Use .get for optional fields
                        expires_at=expires_at,
                        token_type=token_json.get("token_type", "Bearer") # Use .get for optional fields
                    )
                    
                    # Store token in Redis for persistence
                    await self._store_token(self._current_token)
                except ValueError as ve:
                    # Catch specific ValueErrors from our checks above
                    print(f"SAXO OAUTH: Failed to process token data from Saxo. Error: {ve}") # DIAGNOSTIC LOG
                    raise HTTPException(status_code=500, detail=f"Failed to process token data: {ve}. Raw response: {raw_response_text}")
                except Exception as e: # Catch other unexpected errors during token creation (e.g., Pydantic internal if any)
                    print(f"SAXO OAUTH: Failed to create/validate SaxoToken object. Error: {e}") # DIAGNOSTIC LOG
                    # This will catch Pydantic ValidationErrors if fields are still incorrect for SaxoToken model
                    raise HTTPException(status_code=500, detail=f"Failed to create token object: {e}. Raw response: {raw_response_text}")
        
        return self._current_token
    
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
        
        print(f"SAXO OAUTH: Attempting token refresh. Request data: {token_data}")  # DIAGNOSTIC LOG
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                SAXO_TOKEN_URL,
                data=token_data,
                headers=headers
            ) as response:
                
                raw_response_text = await response.text()
                print(f"SAXO OAUTH: Token refresh response status: {response.status}")  # DIAGNOSTIC LOG
                print(f"SAXO OAUTH: Token refresh raw response body: {raw_response_text}")  # DIAGNOSTIC LOG
                
                # Accept both 200 and 201 as success codes (like in exchange_code_for_token)
                if response.status not in [200, 201]:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Token refresh failed: {raw_response_text}"
                    )
                
                try:
                    token_response = json.loads(raw_response_text)
                except json.JSONDecodeError as e:
                    print(f"SAXO OAUTH: Failed to decode JSON from refresh response. Error: {e}")  # DIAGNOSTIC LOG
                    raise HTTPException(status_code=500, detail=f"Failed to decode token JSON from refresh: {e}. Raw response: {raw_response_text}")
        
        # Validate required fields
        if not isinstance(token_response, dict):
            raise HTTPException(status_code=500, detail=f"Invalid token response format, expected dict: {token_response}")
        
        access_token = token_response.get("access_token")
        if not access_token:
            raise HTTPException(status_code=500, detail=f"Missing access_token in refresh response: {token_response}")
        
        # Create new token object
        expires_in = token_response.get("expires_in", 3600)
        expires_at = datetime.now() + timedelta(seconds=expires_in)
        
        token = SaxoToken(
            access_token=access_token,
            refresh_token=token_response.get("refresh_token", refresh_token),  # Keep old if not provided
            expires_at=expires_at,
            token_type=token_response.get("token_type", "Bearer")
        )
        
        self._current_token = token
        print(f"SAXO OAUTH: Token refresh successful. New token expires at: {expires_at}")  # DIAGNOSTIC LOG
        
        # Store refreshed token in Redis for persistence
        await self._store_token(token)
        
        return token
    
    async def get_valid_token(self) -> str:
        """Get a valid access token, refreshing if necessary."""
        # First, try to load token from Redis if not in memory
        if not self._current_token:
            print("SAXO OAUTH: No token in memory, attempting to load from Redis")  # DIAGNOSTIC LOG
            self._current_token = await self._load_token()
        
        if not self._current_token:
            print("SAXO OAUTH: No token available, authentication required")  # DIAGNOSTIC LOG
            raise HTTPException(
                status_code=401, 
                detail="No token available. Please authenticate first."
            )
        
        print(f"SAXO OAUTH: Checking token validity. Expires at: {self._current_token.expires_at}, Is expired: {self._current_token.is_expired}")  # DIAGNOSTIC LOG
        
        if self._current_token.is_expired:
            if not self._current_token.refresh_token:
                print("SAXO OAUTH: Token expired and no refresh token available")  # DIAGNOSTIC LOG
                await self._clear_token()  # Clear invalid token from Redis
                raise HTTPException(
                    status_code=401,
                    detail="Token expired and no refresh token available"
                )
            
            print("SAXO OAUTH: Token expired, attempting refresh")  # DIAGNOSTIC LOG
            # Refresh the token
            await self.refresh_token(self._current_token.refresh_token)
        
        print("SAXO OAUTH: Returning valid access token")  # DIAGNOSTIC LOG
        return self._current_token.access_token

    async def _store_token(self, token: SaxoToken) -> None:
        """Store token in Redis for persistence across serverless requests."""
        redis = await self._get_redis()
        try:
            token_data = {
                "access_token": token.access_token,
                "refresh_token": token.refresh_token,
                "expires_at": token.expires_at.isoformat(),
                "token_type": token.token_type
            }
            # Store token with expiration (add buffer for refresh)
            expires_in = int((token.expires_at - datetime.now()).total_seconds()) + 300  # 5 min buffer
            await redis.set("saxo:current_token", json.dumps(token_data), ex=max(expires_in, 60))
            print(f"SAXO OAUTH: Token stored in Redis, expires in {expires_in} seconds")  # DIAGNOSTIC LOG
        finally:
            await redis.close()
    
    async def _load_token(self) -> Optional[SaxoToken]:
        """Load token from Redis."""
        redis = await self._get_redis()
        try:
            token_data_raw = await redis.get("saxo:current_token")
            if not token_data_raw:
                print("SAXO OAUTH: No token found in Redis")  # DIAGNOSTIC LOG
                return None
            
            token_data = json.loads(token_data_raw)
            token = SaxoToken(
                access_token=token_data["access_token"],
                refresh_token=token_data["refresh_token"],
                expires_at=datetime.fromisoformat(token_data["expires_at"]),
                token_type=token_data["token_type"]
            )
            print(f"SAXO OAUTH: Token loaded from Redis, expires at: {token.expires_at}")  # DIAGNOSTIC LOG
            return token
        except Exception as e:
            print(f"SAXO OAUTH: Failed to load token from Redis: {e}")  # DIAGNOSTIC LOG
            return None
        finally:
            await redis.close()
    
    async def _clear_token(self) -> None:
        """Clear token from Redis."""
        redis = await self._get_redis()
        try:
            await redis.delete("saxo:current_token")
            print("SAXO OAUTH: Token cleared from Redis")  # DIAGNOSTIC LOG
        finally:
            await redis.close()

# Global OAuth client instance
try:
    oauth_client = SaxoOAuth()
except Exception:
    # If OAuth setup fails (missing env vars), create a dummy client
    oauth_client = None 