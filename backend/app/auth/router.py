from __future__ import annotations

import json
import os
from typing import Any, Union

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.responses import RedirectResponse, HTMLResponse
from jose import JWTError, jwt

from market_data.models import PriceResponse, Tick
from storage.redis_client import get_redis
from storage.on_drive import upload_table

# Optional OAuth import - don't break if it fails
try:
    from ..oauth import oauth_client
    OAUTH_AVAILABLE = True
except Exception as e:
    oauth_client = None
    OAUTH_AVAILABLE = False
    print(f"OAuth not available: {e}")

# all paths here (e.g. "/login", "/callback", "/status") will live under "/auth"
router = APIRouter(prefix="/auth")

_bearer = HTTPBearer()


def _verify_jwt(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> None:
    secret = os.environ.get("JWT_SECRET")
    if not secret:
        raise HTTPException(status_code=500, detail="JWT_SECRET not configured")
    token = credentials.credentials
    try:
        jwt.decode(token, secret, algorithms=["HS256"])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def _verify_saxo_token(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> str:
    """Verify SaxoBank OAuth token and return it."""
    if not OAUTH_AVAILABLE:
        raise HTTPException(status_code=500, detail="OAuth not configured")
    
    token = credentials.credentials
    
    # For now, we'll trust that if we have the token and it's the same one
    # stored in our oauth_client, it's valid. In production, you might want
    # to validate it against SaxoBank's token introspection endpoint.
    try:
        # Check if this token matches our stored token
        stored_token = oauth_client._current_token
        if not stored_token or stored_token.access_token != token:
            raise HTTPException(status_code=401, detail="Invalid or expired SaxoBank token")
        
        if stored_token.is_expired:
            raise HTTPException(status_code=401, detail="SaxoBank token expired")
            
        return token
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token validation failed: {str(e)}")


@router.get("/market/price", response_model=PriceResponse)
async def get_market_price(symbol: str, _: str = Depends(_verify_saxo_token)) -> PriceResponse:
    """Get price data using SaxoBank OAuth token."""
    redis = get_redis()
    key = f"fx:{symbol}"
    raw = await redis.get(key)
    await redis.close()
    if not raw:
        raise HTTPException(status_code=404, detail="Symbol not found")
    data = json.loads(raw)
    tick = Tick(**data)
    price = (tick.bid + tick.ask) / 2
    return PriceResponse(symbol=tick.symbol, price=price, timestamp=tick.timestamp)


@router.get("/market/ticks", response_model=list[Tick])
async def get_market_ticks(
    symbol: str,
    since: Union[str, None] = None,
    _: str = Depends(_verify_saxo_token),
) -> list[Tick]:
    """Return cached ticks for symbol using SaxoBank OAuth token."""
    redis = get_redis()
    key = f"ticks:{symbol}"
    raw_ticks = await redis.lrange(key, 0, -1)
    await redis.close()
    if not raw_ticks:
        raise HTTPException(status_code=404, detail="No ticks found")
    ticks = [Tick(**json.loads(item)) for item in raw_ticks]
    if since:
        try:
            cutoff = datetime.fromisoformat(since.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid since timestamp")
        ticks = [
            t
            for t in ticks
            if datetime.fromisoformat(t.timestamp.replace("Z", "+00:00")) >= cutoff
        ]
    return ticks


@router.post("/snapshot", status_code=status.HTTP_202_ACCEPTED)
async def create_snapshot(
    payload: dict[str, list[str]],
    _: Any = Depends(_verify_jwt),
) -> dict[str, str]:
    symbols = payload.get("symbols")
    if not symbols:
        raise HTTPException(status_code=400, detail="symbols required")
    redis = get_redis()
    rows = []
    for sym in symbols:
        raw = await redis.get(f"fx:{sym}")
        if not raw:
            continue
        data = json.loads(raw)
        rows.append(data)
    await redis.close()
    if not rows:
        raise HTTPException(status_code=404, detail="No data for symbols")
    import pyarrow as pa

    table = pa.Table.from_pylist(rows)
    now = datetime.now(timezone.utc).isoformat().replace(":", "-")
    path = f"snapshots/{now}.parquet"
    await upload_table(table, path)
    return {"detail": "snapshot scheduled", "path": path}


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint for deployment monitoring."""
    return {"status": "healthy", "service": "JH Market Data API"}


@router.get("/debug")
async def debug_info() -> dict[str, Any]:
    """Debug endpoint to check what's available."""
    return {
        "status": "ok",
        "oauth_available": OAUTH_AVAILABLE,
        "environment_vars": {
            "JWT_SECRET": "SET" if os.environ.get("JWT_SECRET") else "NOT_SET",
            "REDIS_URL": "SET" if os.environ.get("REDIS_URL") else "NOT_SET",
            "SAXO_APP_KEY": "SET" if os.environ.get("SAXO_APP_KEY") else "NOT_SET",
        }
    }


@router.get("/login")
async def initiate_oauth() -> dict[str, str]:
    """Initiate OAuth flow with SaxoBank."""
    if not OAUTH_AVAILABLE:
        raise HTTPException(
            status_code=500, 
            detail="OAuth not configured. Missing environment variables: SAXO_APP_KEY, SAXO_APP_SECRET, SAXO_REDIRECT_URI"
        )
    
    try:
        auth_url, state = oauth_client.get_authorization_url()
        return {
            "auth_url": auth_url,
            "state": state,
            "message": "Visit auth_url to complete authentication"
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OAuth setup failed: {str(e)}")


@router.get("/callback")
async def oauth_callback(
    code: str = Query(..., description="Authorization code from SaxoBank"),
    state: str = Query(..., description="State parameter for validation")
) -> HTMLResponse:
    """Handle OAuth callback from SaxoBank."""
    if not OAUTH_AVAILABLE:
        return HTMLResponse(
            content="""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Authentication Error</title>
            </head>
            <body>
                <h2>Authentication Failed</h2>
                <p>OAuth not configured. Missing environment variables.</p>
                <p><a href="/">Return to application</a></p>
            </body>
            </html>
            """,
            status_code=500
        )
        
    try:
        # Exchange code for token
        token = await oauth_client.exchange_code_for_token(code, state)
        
        # Create success HTML response
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authentication Success</title>
            <script>
                // Remove any URL fragments before processing
                if (window.location.hash) {
                    window.history.replaceState(null, '', window.location.pathname + window.location.search);
                }
            </script>
        </head>
        <body>
            <h2>Authentication Successful!</h2>
            <p>You can close this window and return to the application.</p>
            <script>
                // If this is a popup, close it and notify parent
                if (window.opener) {
                    window.opener.postMessage({
                        type: 'SAXO_AUTH_SUCCESS',
                        token: '""" + token.access_token + """',
                        expires_at: '""" + token.expires_at.isoformat() + """'
                    }, '*');
                    window.close();
                } else {
                    // If not a popup, redirect to main app
                    setTimeout(() => {
                        window.location.href = '/';
                    }, 2000);
                }
            </script>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
        
    except HTTPException as e:
        # Create error HTML response
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authentication Error</title>
            <script>
                // Remove any URL fragments before processing
                if (window.location.hash) {{
                    window.history.replaceState(null, '', window.location.pathname + window.location.search);
                }}
            </script>
        </head>
        <body>
            <h2>Authentication Failed</h2>
            <p>{e.detail}</p>
            <p><a href="/">Return to application</a></p>
            <script>
                // If this is a popup, notify parent of error
                if (window.opener) {{
                    window.opener.postMessage({{
                        type: 'SAXO_AUTH_ERROR',
                        error: '{e.detail}'
                    }}, '*');
                }}
            </script>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content, status_code=e.status_code)
        
    except Exception as e:
        # Create error HTML response
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authentication Error</title>
            <script>
                // Remove any URL fragments before processing
                if (window.location.hash) {{
                    window.history.replaceState(null, '', window.location.pathname + window.location.search);
                }}
            </script>
        </head>
        <body>
            <h2>Authentication Failed</h2>
            <p>OAuth callback failed: {str(e)}</p>
            <p><a href="/">Return to application</a></p>
            <script>
                // If this is a popup, notify parent of error
                if (window.opener) {{
                    window.opener.postMessage({{
                        type: 'SAXO_AUTH_ERROR',
                        error: 'OAuth callback failed: {str(e)}'
                    }}, '*');
                }}
            </script>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content, status_code=500)


@router.get("/status")
async def auth_status() -> dict[str, Any]:
    """Check current authentication status."""
    if not OAUTH_AVAILABLE:
        return {
            "authenticated": False,
            "message": "OAuth not configured. Missing environment variables."
        }
        
    try:
        # This will raise an exception if no token or token expired
        token = await oauth_client.get_valid_token()
        return {
            "authenticated": True,
            "message": "Valid token available"
        }
    except HTTPException as e:
        return {
            "authenticated": False,
            "message": e.detail
        }
    except Exception as e:
        return {
            "authenticated": False,
            "message": f"Authentication check failed: {str(e)}"
        }


@router.get("/price", response_model=PriceResponse)
async def get_price(symbol: str, _: Any = Depends(_verify_jwt)) -> PriceResponse:
    """Get price data using internal JWT token."""
    redis = get_redis()
    key = f"fx:{symbol}"
    raw = await redis.get(key)
    await redis.close()
    if not raw:
        raise HTTPException(status_code=404, detail="Symbol not found")
    data = json.loads(raw)
    tick = Tick(**data)
    price = (tick.bid + tick.ask) / 2
    return PriceResponse(symbol=tick.symbol, price=price, timestamp=tick.timestamp)


@router.get("/ticks", response_model=list[Tick])
async def get_ticks(
    symbol: str,
    since: Union[str, None] = None,
    _: Any = Depends(_verify_jwt),
) -> list[Tick]:
    """Return cached ticks for symbol using internal JWT token."""
    redis = get_redis()
    key = f"ticks:{symbol}"
    raw_ticks = await redis.lrange(key, 0, -1)
    await redis.close()
    if not raw_ticks:
        raise HTTPException(status_code=404, detail="No ticks found")
    ticks = [Tick(**json.loads(item)) for item in raw_ticks]
    if since:
        try:
            cutoff = datetime.fromisoformat(since.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid since timestamp")
        ticks = [
            t
            for t in ticks
            if datetime.fromisoformat(t.timestamp.replace("Z", "+00:00")) >= cutoff
        ]
    return ticks


@router.get("/debug/redis")
async def debug_redis() -> dict[str, Any]:
    """Debug endpoint to check what's in Redis."""
    redis = get_redis()
    try:
        # Get all fx: keys
        fx_keys = []
        async for key in redis.scan_iter(match="fx:*"):
            fx_keys.append(key.decode() if isinstance(key, bytes) else key)
        
        # Get all ticks: keys  
        tick_keys = []
        async for key in redis.scan_iter(match="ticks:*"):
            tick_keys.append(key.decode() if isinstance(key, bytes) else key)
            
        # Sample some data
        sample_data = {}
        for key in fx_keys[:5]:  # Sample first 5
            raw = await redis.get(key)
            if raw:
                sample_data[key] = json.loads(raw)
                
        return {
            "fx_keys_count": len(fx_keys),
            "fx_keys": fx_keys,
            "tick_keys_count": len(tick_keys), 
            "tick_keys": tick_keys,
            "sample_data": sample_data
        }
    finally:
        await redis.close()


@router.get("/service/status")
async def get_service_status() -> dict[str, Any]:
    """Get real-time market data service status."""
    redis = get_redis()
    try:
        # Get service status
        status_raw = await redis.get("service:market_data:status")
        heartbeat_raw = await redis.get("service:market_data:heartbeat")
        
        # Parse status
        service_status = "unknown"
        restart_count = 0
        last_update = None
        symbols = []
        
        if status_raw:
            try:
                # Simple parsing since we stored it as string representation
                status_str = status_raw.replace('"', "'")
                if "'status': '" in status_str:
                    service_status = status_str.split("'status': '")[1].split("'")[0]
                if "'restart_count': " in status_str:
                    restart_count = int(status_str.split("'restart_count': ")[1].split(",")[0])
                if "'timestamp': '" in status_str:
                    last_update = status_str.split("'timestamp': '")[1].split("'")[0]
            except:
                pass
        
        # Check heartbeat
        heartbeat_age = None
        if heartbeat_raw:
            try:
                from datetime import datetime, timezone
                heartbeat_time = datetime.fromisoformat(heartbeat_raw.replace('Z', '+00:00'))
                current_time = datetime.now(timezone.utc)
                heartbeat_age = (current_time - heartbeat_time).total_seconds()
            except:
                pass
        
        # Determine overall health
        is_healthy = (
            service_status in ["running", "starting"] and
            heartbeat_age is not None and
            heartbeat_age < 120  # Less than 2 minutes old
        )
        
        return {
            "service_status": service_status,
            "is_healthy": is_healthy,
            "restart_count": restart_count,
            "last_update": last_update,
            "heartbeat_age_seconds": heartbeat_age,
            "symbols_monitored": [
                'EUR-USD', 'GBP-USD', 'USD-JPY', 'AUD-USD', 
                'USD-CHF', 'USD-CAD', 'NZD-USD'
            ]
        }
        
    finally:
        await redis.close()
