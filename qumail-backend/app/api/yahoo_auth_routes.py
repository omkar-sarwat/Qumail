"""
Yahoo OAuth Routes for Yahoo Mail
Handles authentication and callback for Yahoo accounts

Note: Yahoo requires HTTPS redirect URIs
- Use https://127.0.0.1:5173/auth/yahoo/callback for local development
- For production, use your HTTPS domain
"""

from fastapi import APIRouter, HTTPException, Request, Query, status
from fastapi.responses import RedirectResponse
from typing import Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import logging
import secrets

from ..services.yahoo_oauth import yahoo_oauth_service, YahooOAuthError, YahooTokenError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/auth/yahoo", tags=["Yahoo OAuth"])


class YahooAuthStartResponse(BaseModel):
    """Response for starting Yahoo OAuth flow"""
    authorization_url: str
    state: str
    redirect_uri: str
    note: str = "Yahoo requires HTTPS. Use https://127.0.0.1:5173 for local dev."


class YahooAuthCallbackResponse(BaseModel):
    """Response for Yahoo OAuth callback"""
    success: bool
    user_email: str
    display_name: str
    access_token: str
    refresh_token: str
    expires_at: str
    provider: str = "yahoo"
    message: str = "Yahoo authentication successful"


class YahooAuthStatusResponse(BaseModel):
    """Response for Yahoo OAuth configuration status"""
    configured: bool
    message: str
    redirect_uri: str


@router.get("/status", response_model=YahooAuthStatusResponse)
async def check_yahoo_oauth_status():
    """
    Check if Yahoo OAuth is configured
    
    Use this to determine whether to show the "Login with Yahoo" button
    """
    is_configured = yahoo_oauth_service.is_configured()
    
    return YahooAuthStatusResponse(
        configured=is_configured,
        message="Yahoo OAuth is configured" if is_configured else "Yahoo OAuth not configured. Set YAHOO_CLIENT_ID and YAHOO_CLIENT_SECRET.",
        redirect_uri=yahoo_oauth_service.redirect_uri
    )


@router.get("/login", response_model=YahooAuthStartResponse)
async def yahoo_oauth_login(
    request: Request,
    user_id: Optional[str] = Query(None, description="Optional user ID for state tracking"),
    redirect_type: str = Query("localhost", description="Redirect URI type: localhost, netlify, vercel, oob")
):
    """
    Get Yahoo OAuth authorization URL
    
    Redirects user to Yahoo login page for Yahoo Mail access.
    
    IMPORTANT: Yahoo requires HTTPS redirect URIs!
    - For localhost: Use https://127.0.0.1:5173/auth/yahoo/callback
    - Configure this in your Yahoo Developer Console
    
    Security Features:
    - CSRF protection with state parameter
    - Offline access for refresh tokens
    """
    try:
        # Check if Yahoo OAuth is configured
        if not yahoo_oauth_service.is_configured():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Yahoo OAuth not configured. Set YAHOO_CLIENT_ID and YAHOO_CLIENT_SECRET environment variables."
            )
        
        # Generate authorization URL
        auth_data = yahoo_oauth_service.generate_authorization_url(
            user_id=user_id,
            redirect_uri_type=redirect_type
        )
        
        logger.info(f"Yahoo OAuth login initiated for redirect type: {redirect_type}")
        
        return YahooAuthStartResponse(
            authorization_url=auth_data["authorization_url"],
            state=auth_data["state"],
            redirect_uri=auth_data["redirect_uri"],
            note="Yahoo requires HTTPS. Make sure your redirect URI uses https://127.0.0.1 for local development."
        )
        
    except YahooOAuthError as e:
        logger.error(f"Yahoo OAuth error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in Yahoo OAuth login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate Yahoo OAuth"
        )


@router.get("/callback")
async def yahoo_oauth_callback(
    code: Optional[str] = Query(None, description="Authorization code from Yahoo"),
    state: Optional[str] = Query(None, description="CSRF state token"),
    error: Optional[str] = Query(None, description="Error code if auth failed"),
    error_description: Optional[str] = Query(None, description="Error description")
):
    """
    Handle Yahoo OAuth callback
    
    This endpoint receives the authorization code from Yahoo after user consent.
    It exchanges the code for access and refresh tokens.
    """
    try:
        # Check for errors from Yahoo
        if error:
            logger.error(f"Yahoo OAuth error: {error} - {error_description}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Yahoo authentication failed: {error_description or error}"
            )
        
        # Validate required parameters
        if not code or not state:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing authorization code or state parameter"
            )
        
        # Verify state to prevent CSRF
        state_data = yahoo_oauth_service.verify_state(state)
        if not state_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired state parameter. Please try again."
            )
        
        # Exchange code for tokens
        tokens = await yahoo_oauth_service.exchange_code_for_tokens(
            code=code,
            redirect_uri=state_data.get("redirect_uri")
        )
        
        # Get user info
        user_info = await yahoo_oauth_service.get_user_info(tokens["access_token"])
        
        # Calculate token expiration
        expires_at = datetime.utcnow() + timedelta(seconds=tokens.get("expires_in", 3600))
        
        logger.info(f"Yahoo OAuth successful for: {user_info.get('email')}")
        
        return YahooAuthCallbackResponse(
            success=True,
            user_email=user_info.get("email", ""),
            display_name=user_info.get("name", user_info.get("email", "Yahoo User")),
            access_token=tokens["access_token"],
            refresh_token=tokens.get("refresh_token", ""),
            expires_at=expires_at.isoformat(),
            provider="yahoo",
            message="Yahoo authentication successful! You can now access your Yahoo Mail."
        )
        
    except YahooTokenError as e:
        logger.error(f"Yahoo token error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except YahooOAuthError as e:
        logger.error(f"Yahoo OAuth error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in Yahoo OAuth callback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete Yahoo authentication: {str(e)}"
        )


@router.post("/callback")
async def yahoo_oauth_callback_post(
    code: str,
    state: str,
    redirect_uri: Optional[str] = None
):
    """
    Handle Yahoo OAuth callback via POST (for frontend)
    
    Frontend can POST the authorization code directly instead of redirecting.
    """
    try:
        # Verify state
        state_data = yahoo_oauth_service.verify_state(state)
        if not state_data:
            # State might have been consumed or not found
            # Allow proceeding if redirect_uri is provided
            state_data = {"redirect_uri": redirect_uri or yahoo_oauth_service.redirect_uri}
        
        # Exchange code for tokens
        tokens = await yahoo_oauth_service.exchange_code_for_tokens(
            code=code,
            redirect_uri=state_data.get("redirect_uri") or redirect_uri
        )
        
        # Get user info
        user_info = await yahoo_oauth_service.get_user_info(tokens["access_token"])
        
        # Calculate token expiration
        expires_at = datetime.utcnow() + timedelta(seconds=tokens.get("expires_in", 3600))
        
        logger.info(f"Yahoo OAuth (POST) successful for: {user_info.get('email')}")
        
        return YahooAuthCallbackResponse(
            success=True,
            user_email=user_info.get("email", ""),
            display_name=user_info.get("name", user_info.get("email", "Yahoo User")),
            access_token=tokens["access_token"],
            refresh_token=tokens.get("refresh_token", ""),
            expires_at=expires_at.isoformat(),
            provider="yahoo",
            message="Yahoo authentication successful!"
        )
        
    except YahooTokenError as e:
        logger.error(f"Yahoo token error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in Yahoo OAuth callback POST: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete Yahoo authentication: {str(e)}"
        )


@router.post("/refresh")
async def refresh_yahoo_token(refresh_token: str):
    """
    Refresh Yahoo access token
    
    Use this when the access token expires to get a new one.
    """
    try:
        tokens = await yahoo_oauth_service.refresh_access_token(refresh_token)
        
        expires_at = datetime.utcnow() + timedelta(seconds=tokens.get("expires_in", 3600))
        
        return {
            "success": True,
            "access_token": tokens["access_token"],
            "refresh_token": tokens.get("refresh_token", refresh_token),
            "expires_at": expires_at.isoformat(),
            "message": "Token refreshed successfully"
        }
        
    except YahooTokenError as e:
        logger.error(f"Yahoo token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error refreshing Yahoo token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh token"
        )


@router.post("/logout")
async def yahoo_logout(access_token: Optional[str] = None):
    """
    Logout from Yahoo (revoke tokens if possible)
    
    Note: Yahoo tokens expire automatically, this mainly clears local state.
    """
    try:
        if access_token:
            await yahoo_oauth_service.revoke_token(access_token)
        
        return {
            "success": True,
            "message": "Yahoo logout successful"
        }
        
    except Exception as e:
        logger.error(f"Error during Yahoo logout: {e}")
        # Don't fail logout
        return {
            "success": True,
            "message": "Logout completed"
        }
