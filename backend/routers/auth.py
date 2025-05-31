# backend/routers/auth.py

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from core.deps import get_settings, get_logger, get_redis
from services.oauth_client import SaxoOAuthClient, SaxoToken # Corrected import
from redis.asyncio import Redis
import logging

# Singleton logger
logger = get_logger()

router = APIRouter(prefix="/api/auth")

# Dependency for SaxoOAuthClient
# No longer instantiating SaxoOAuthClient directly in routes
# Instead, it will be injected by FastAPI's dependency injection system.

@router.get("/login", summary="Initiate SaxoBank OAuth flow")
async def login_saxo(
    request: Request,
    oauth_client: SaxoOAuthClient = Depends(SaxoOAuthClient) # Use dependency injection
):
    logger = logging.getLogger("jh")
    logger.info("/api/auth/login endpoint called")
    try:
        # The get_authorization_url method now correctly returns the auth_url and state
        auth_url, state = await oauth_client.get_authorization_url()
        logger.info(f"Obtained auth_url: {auth_url}, state: {state}")
        # Store state in session or a secure cookie if preferred
        # For simplicity here, we assume the client might handle it or it's passed through
        request.session["oauth_state"] = state # Example: Storing state in session
        return RedirectResponse(url=auth_url)
    except HTTPException as e:
        logger.error(f"HTTPException in /api/auth/login: {e.detail}")
        # Re-raise HTTPExceptions directly
        raise e
    except Exception as e:
        logger.exception("Unhandled exception in /api/auth/login endpoint")
        # Log the exception details for debugging
        # logger.error(f"SaxoBank Authentication - Failed to initiate authentication: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SaxoBank Authentication - Failed to initiate authentication: {str(e)}"
        )

@router.get("/callback", summary="SaxoBank OAuth callback")
async def callback_saxo(
    request: Request, # Moved before arguments with default values
    code: str = Query(...),
    state: str = Query(...), # Added state parameter to match Saxo's callback
    oauth_client: SaxoOAuthClient = Depends(SaxoOAuthClient) # Use dependency injection
):
    """
    Handles the callback from SaxoBank after user authentication.
    Exchanges the authorization code for an access token and stores it.
    """
    # Example: Retrieve state from session if you stored it there
    # stored_state = request.session.pop("oauth_state", None)
    # if not stored_state or stored_state != state:
    #     raise HTTPException(status_code=400, detail="Invalid OAuth state or state mismatch")

    try:
        # The exchange_code_for_token method now handles state validation,
        # token parsing, and Redis storage internally.
        token: SaxoToken = await oauth_client.exchange_code_for_token(code=code, state=state)

        # Redirect to frontend or return token info
        # The frontend URL should be configurable, e.g., from settings
        frontend_url = request.app.state.settings.FRONTEND_REDIRECT_URL # Access settings via app.state
        # You might want to pass the token or a session cookie to the frontend
        # For now, just redirecting to a success page or the main app page
        # return RedirectResponse(url=f"{frontend_url}?status=success")
        # Alternatively, return token information if the frontend expects it
        return {
            "message": "Authentication successful",
            "access_token_expires_at": token.expires_at.isoformat(),
            # Avoid sending the actual tokens to the client unless absolutely necessary
            # and handled securely (e.g., via secure, HttpOnly cookies).
        }
    except HTTPException as e:
        # Re-raise HTTPExceptions directly (e.g., from state validation or token exchange)
        raise e
    except Exception as e:
        # Log the exception details for debugging
        # logger.error(f"SaxoBank Authentication - Failed to process callback: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SaxoBank Authentication - Failed to process callback: {str(e)}"
        )

@router.get("/token", summary="Get current Saxo access token", response_model=SaxoToken)
async def get_current_token(
    oauth_client: SaxoOAuthClient = Depends(SaxoOAuthClient) # Use dependency injection
):
    """
    Retrieves the current valid Saxo access token.
    If the token is expired or not found, it attempts to refresh it or raises an error.
    """
    try:
        # get_valid_token in SaxoOAuthClient handles fetching/refreshing
        access_token_str = await oauth_client.get_valid_token() # This returns the string token
        # If you need the full SaxoToken object, you might need to adjust get_valid_token
        # or retrieve it from Redis again and parse. For simplicity, assuming the string is enough
        # or that the client primarily needs to know if a valid token *can* be obtained.

        # For the purpose of this endpoint, if get_valid_token succeeds,
        # it means a valid token is available or was refreshed.
        # We might want to return more info, or the token itself if appropriate.
        # Let's assume we want to return the token details as stored.
        stored_token_data = await oauth_client.redis.get("saxo:current_token")
        if not stored_token_data:
            raise HTTPException(status_code=404, detail="Token not found after validation attempt.")
        
        token = SaxoToken.parse_raw(stored_token_data)
        return token
    except HTTPException as e:
        raise e
    except Exception as e:
        # logger.error(f"SaxoBank Authentication - Failed to retrieve token: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SaxoBank Authentication - Failed to retrieve token: {str(e)}"
        )

# ... any other routes or code ...
