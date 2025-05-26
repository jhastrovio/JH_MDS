from __future__ import annotations

import json
import os
from typing import Any

from datetime import datetime, UTC
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.responses import RedirectResponse, HTMLResponse
from jose import JWTError, jwt

from market_data.models import PriceResponse, Tick
from storage.redis_client import get_redis
from storage.on_drive import upload_table

# Optional OAuth import - don't break if it fails
try:
    from .oauth import oauth_client
    OAUTH_AVAILABLE = True
except Exception as e:
    oauth_client = None
    OAUTH_AVAILABLE = False
    print(f"OAuth not available: {e}")

router = APIRouter(prefix="/api")

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


@router.get("/price", response_model=PriceResponse)
async def get_price(symbol: str, _: Any = Depends(_verify_jwt)) -> PriceResponse:
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
    since: str | None = None,
    _: Any = Depends(_verify_jwt),
) -> list[Tick]:
    """Return cached ticks for ``symbol`` optionally filtered by ``since``."""
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
    now = datetime.now(UTC).isoformat().replace(":", "-")
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


@router.get("/auth/login")
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


@router.get("/auth/callback")
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
        </head>
        <body>
            <h2>Authentication Successful!</h2>
            <p>You can close this window and return to the application.</p>
            <script>
                // If this is a popup, close it and notify parent
                if (window.opener) {
                    window.opener.postMessage({
                        type: 'SAXO_AUTH_SUCCESS',
                        token: true,
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


@router.get("/auth/status")
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
