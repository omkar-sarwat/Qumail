"""
Microsoft OAuth Routes for Outlook/Microsoft 365
Handles authentication and callback for Microsoft accounts
"""

from fastapi import APIRouter, HTTPException, Request, Query, Depends, status
from fastapi.responses import RedirectResponse
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional
from pydantic import BaseModel
import logging

from ..mongo_database import get_database
from ..services.microsoft_oauth import microsoft_oauth_service, MicrosoftOAuthError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/auth/microsoft", tags=["Microsoft OAuth"])


class MicrosoftAuthStartResponse(BaseModel):
    """Response for starting Microsoft OAuth flow"""
    authorization_url: str
    state: str


class MicrosoftAuthCallbackResponse(BaseModel):
    """Response for Microsoft OAuth callback"""
    success: bool
    user_email: str
    display_name: str
    session_token: str
    expires_at: str
    provider: str
    message: str = "Microsoft authentication successful"


class MicrosoftAuthStatusResponse(BaseModel):
    """Response for Microsoft OAuth configuration status"""
    configured: bool
    message: str


@router.get("/status", response_model=MicrosoftAuthStatusResponse)
async def check_microsoft_oauth_status():
    """
    Check if Microsoft OAuth is configured
    
    Use this to determine whether to show the "Login with Outlook" button
    """
    is_configured = microsoft_oauth_service.is_configured()
    
    return MicrosoftAuthStatusResponse(
        configured=is_configured,
        message="Microsoft OAuth is configured" if is_configured else "Microsoft OAuth not configured. Set MICROSOFT_CLIENT_ID and MICROSOFT_CLIENT_SECRET environment variables."
    )


@router.get("/login", response_model=MicrosoftAuthStartResponse)
async def microsoft_oauth_login(
    request: Request,
    user_id: Optional[str] = Query(None, description="Optional user ID for state tracking"),
    is_electron: bool = Query(False, description="Whether request is from Electron app")
):
    """
    Get Microsoft OAuth authorization URL
    
    Redirects user to Microsoft login page for Outlook/Microsoft 365 access.
    
    Security Features:
    - CSRF protection with state parameter
    - Offline access for refresh tokens
    - Account picker for multiple Microsoft accounts
    """
    try:
        # Check if Microsoft OAuth is configured
        if not microsoft_oauth_service.is_configured():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Microsoft OAuth not configured. Contact administrator."
            )
        
        # Get origin from request headers
        origin = None
        try:
            from urllib.parse import urlparse
            raw_origin = request.headers.get("origin")
            raw_referer = request.headers.get("referer", "")
            origin = raw_origin or (raw_referer.rstrip("/") if raw_referer else None)
            if origin and "://" in origin:
                parsed = urlparse(origin)
                if parsed.scheme and parsed.netloc:
                    origin = f"{parsed.scheme}://{parsed.netloc}"
            logger.info(f"Parsed origin: {origin} from raw_origin={raw_origin}")
        except Exception as parse_error:
            logger.warning(f"Failed to parse origin: {parse_error}")
            origin = None
        
        auth_data = microsoft_oauth_service.generate_authorization_url(
            user_id=user_id,
            is_electron=is_electron,
            origin=origin
        )
        
        logger.info(f"Generated Microsoft OAuth URL for user: {user_id}, origin: {origin}")
        
        return MicrosoftAuthStartResponse(
            authorization_url=auth_data["authorization_url"],
            state=auth_data["state"]
        )
    
    except MicrosoftOAuthError as e:
        logger.error(f"Microsoft OAuth error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    
    except Exception as e:
        logger.error(f"Error generating Microsoft OAuth URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate Microsoft authorization URL"
        )


@router.get("/callback", response_model=MicrosoftAuthCallbackResponse)
async def microsoft_oauth_callback(
    code: str = Query(..., description="Authorization code from Microsoft"),
    state: str = Query(..., description="State parameter for CSRF protection"),
    error: Optional[str] = Query(None, description="OAuth error if any"),
    error_description: Optional[str] = Query(None, description="Error description"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Handle Microsoft OAuth callback
    
    Exchanges authorization code for tokens and creates/updates user account.
    
    Security Features:
    - State parameter validation (CSRF protection)
    - Secure token exchange
    - Encrypted token storage
    """
    # Check for OAuth errors
    if error:
        logger.error(f"Microsoft OAuth callback error: {error} - {error_description}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Microsoft OAuth authorization failed: {error_description or error}"
        )
    
    try:
        # Exchange code for tokens
        token_data = await microsoft_oauth_service.exchange_code_for_tokens(
            authorization_code=code,
            state=state,
            db=db
        )
        
        logger.info(f"Microsoft OAuth successful for user: {token_data['user_email']}")
        
        return MicrosoftAuthCallbackResponse(
            success=True,
            user_email=token_data["user_email"],
            display_name=token_data["display_name"],
            session_token=token_data["session_token"],
            expires_at=token_data["expires_at"],
            provider=token_data["provider"],
            message="Microsoft authentication successful"
        )
    
    except MicrosoftOAuthError as e:
        logger.error(f"Microsoft OAuth error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except Exception as e:
        logger.error(f"Unexpected Microsoft OAuth error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Microsoft authentication failed due to system error"
        )


@router.post("/refresh")
async def refresh_microsoft_token(
    user_email: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Refresh Microsoft access token
    
    Use this when the access token has expired.
    """
    try:
        new_access_token = await microsoft_oauth_service.refresh_access_token(
            user_email=user_email,
            db=db
        )
        
        logger.info(f"Microsoft token refreshed for user: {user_email}")
        
        return {
            "success": True,
            "message": "Token refreshed successfully"
        }
    
    except MicrosoftOAuthError as e:
        logger.error(f"Microsoft token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/debug/states")
async def debug_microsoft_oauth_states():
    """Debug endpoint to check Microsoft OAuth states (remove in production)"""
    from datetime import datetime
    
    states = {}
    for state, data in microsoft_oauth_service._oauth_states.items():
        states[state] = {
            "created_at": data["created_at"].isoformat(),
            "expires_at": data["expires_at"].isoformat(),
            "is_expired": data["expires_at"] < datetime.utcnow()
        }
    return {"states": states, "total": len(states)}
