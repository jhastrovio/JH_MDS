# backend/routers/auth.py

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from core.deps import get_logger
from services.oauth_client import SaxoOAuthClient, SaxoToken

router = APIRouter(prefix="/api/auth")
logger = get_logger()

@router.get("/login", summary="Initiate SaxoBank OAuth flow")
async def login_saxo(
    request: Request,
    oauth_client: SaxoOAuthClient = Depends(SaxoOAuthClient)
):
    """
    Initiates the SaxoBank OAuth flow and redirects the user to the authorization URL.
    """
    logger.info("/api/auth/login endpoint called")
    try:
        auth_url, state = await oauth_client.get_authorization_url()
        logger.info(f"Obtained auth_url: {auth_url}, state: {state}")
        request.session["oauth_state"] = state
        return RedirectResponse(url=auth_url)
    except HTTPException as e:
        logger.error(f"HTTPException in /api/auth/login: {e.detail}")
        raise e
    except Exception as e:
        logger.exception("Unhandled exception in /api/auth/login endpoint")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SaxoBank Authentication - Failed to initiate authentication: {str(e)}"
        )

@router.get("/callback", summary="SaxoBank OAuth callback")
async def callback_saxo(
    request: Request,
    code: str = Query(...),
    state: str = Query(...),
    oauth_client: SaxoOAuthClient = Depends(SaxoOAuthClient)
):
    """
    Handles the callback from SaxoBank after user authentication.
    Exchanges the authorization code for an access token and stores it.
    Redirects to the frontend on success.
    """
    try:
        await oauth_client.exchange_code_for_token(code=code, state=state)
        frontend_url = request.app.state.settings.NEXT_PUBLIC_API_URL
        return RedirectResponse(url=f"{frontend_url}?status=success")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SaxoBank Authentication - Failed to process callback: {str(e)}"
        )

@router.get("/token", summary="Get current Saxo access token", response_model=SaxoToken)
async def get_current_token(
    oauth_client: SaxoOAuthClient = Depends(SaxoOAuthClient)
):
    """
    Retrieves the current valid Saxo access token.
    If the token is expired or not found, it attempts to refresh it or raises an error.
    """
    try:
        await oauth_client.get_valid_token()
        stored_token_data = await oauth_client.redis.get("saxo:current_token")
        if not stored_token_data:
            raise HTTPException(status_code=404, detail="Token not found after validation attempt.")
        token = SaxoToken.parse_raw(stored_token_data)
        return token
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SaxoBank Authentication - Failed to retrieve token: {str(e)}"
        )

@router.get("/status", summary="Get Saxo authentication status")
async def auth_status(
    oauth_client: SaxoOAuthClient = Depends(SaxoOAuthClient)
):
    """
    Returns authentication status for SaxoBank.
    """
    try:
        await oauth_client.get_valid_token()
        return {"authenticated": True, "message": "Authenticated"}
    except HTTPException as e:
        if e.status_code == 401:
            return {"authenticated": False, "message": "Not authenticated"}
        raise
    except Exception as e:
        return {"authenticated": False, "message": f"Error: {str(e)}"}
