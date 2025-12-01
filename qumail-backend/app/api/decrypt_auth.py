"""
Decrypt Authentication API - Google Authenticator TOTP verification for email decryption.

Flow:
1. First decrypt - Uses quantum keys (as usual)
2. Subsequent decrypts - Requires TOTP code from Google Authenticator

The TOTP secret is tied to the user's Google OAuth account email.
"""
from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import logging

from ..mongo_database import get_database
from ..mongo_models import UserDocument
from ..services.totp_service import totp_service
from .auth import get_current_user

router = APIRouter(prefix="/api/v1/decrypt-auth", tags=["decrypt-auth"])
logger = logging.getLogger(__name__)


# ============================================
# Request/Response Models
# ============================================

class Setup2FAForDecryptResponse(BaseModel):
    """Response for 2FA setup"""
    qr_code: str  # Base64 PNG image
    secret: str  # Manual entry secret
    message: str
    already_setup: bool = False


class Verify2FASetupRequest(BaseModel):
    """Request to verify 2FA setup with initial code"""
    code: str  # 6-digit code from Google Authenticator


class Verify2FASetupResponse(BaseModel):
    """Response after verifying 2FA setup"""
    success: bool
    message: str


class VerifyDecryptTOTPRequest(BaseModel):
    """Request to verify TOTP for decrypt access"""
    code: str  # 6-digit code from Google Authenticator
    email_id: str  # Email being decrypted


class VerifyDecryptTOTPResponse(BaseModel):
    """Response after verifying TOTP for decrypt"""
    success: bool
    message: str
    valid_until: Optional[datetime] = None  # Session valid until this time


class DecryptAuthStatusResponse(BaseModel):
    """Response for decrypt auth status check"""
    totp_setup: bool  # Whether user has set up TOTP
    totp_verified: bool  # Whether TOTP is verified and active
    user_email: str


# ============================================
# API Endpoints
# ============================================

@router.get("/status", response_model=DecryptAuthStatusResponse)
async def get_decrypt_auth_status(
    current_user: UserDocument = Depends(get_current_user)
):
    """
    Check if user has TOTP set up for decrypt authentication.
    This is tied to the user's Google account email.
    """
    return DecryptAuthStatusResponse(
        totp_setup=bool(current_user.totp_secret),
        totp_verified=current_user.totp_verified,
        user_email=current_user.email
    )


@router.post("/setup", response_model=Setup2FAForDecryptResponse)
async def setup_decrypt_2fa(
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Set up Google Authenticator for decrypt verification.
    Returns QR code to scan with Google Authenticator app.
    
    The account name in the authenticator will be the user's Google email.
    """
    try:
        # Check if already set up
        if current_user.totp_secret and current_user.totp_verified:
            # Already set up - generate new QR code for viewing
            totp_secret = totp_service.decrypt_secret(current_user.totp_secret)
            qr_code = totp_service.generate_qr_code(totp_secret, current_user.email)
            
            return Setup2FAForDecryptResponse(
                qr_code=qr_code,
                secret=totp_secret,
                message="Google Authenticator is already set up. Here's your QR code for reference.",
                already_setup=True
            )
        
        # Generate new 2FA setup
        setup_data = totp_service.setup_2fa(current_user.email)
        
        # Store encrypted secret (not verified yet)
        await db.users.update_one(
            {"_id": current_user.id},
            {"$set": {
                "totp_secret": setup_data["secret"],
                "totp_verified": False,
                "totp_enabled": True
            }}
        )
        
        logger.info(f"🔐 Decrypt 2FA setup initiated for user: {current_user.email}")
        
        return Setup2FAForDecryptResponse(
            qr_code=setup_data["qr_code"],
            secret=setup_data["secret_plain"],
            message="Scan this QR code with Google Authenticator. Then verify with a 6-digit code."
        )
        
    except Exception as e:
        logger.error(f"Failed to setup decrypt 2FA: {e}")
        raise HTTPException(status_code=500, detail="Failed to setup Google Authenticator")


@router.post("/verify-setup", response_model=Verify2FASetupResponse)
async def verify_decrypt_2fa_setup(
    request: Verify2FASetupRequest,
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Verify initial TOTP setup by entering a code from Google Authenticator.
    This activates TOTP for decrypt operations.
    """
    try:
        if not current_user.totp_secret:
            raise HTTPException(status_code=400, detail="Please set up Google Authenticator first")
        
        if current_user.totp_verified:
            return Verify2FASetupResponse(
                success=True,
                message="Google Authenticator is already verified and active."
            )
        
        # Decrypt and verify
        totp_secret = totp_service.decrypt_secret(current_user.totp_secret)
        code = request.code.replace(" ", "").strip()
        
        is_valid = totp_service.verify_totp(totp_secret, code)
        
        if not is_valid:
            raise HTTPException(status_code=400, detail="Invalid code. Please try again.")
        
        # Mark as verified
        await db.users.update_one(
            {"_id": current_user.id},
            {"$set": {
                "totp_verified": True
            }}
        )
        
        logger.info(f"✅ Decrypt 2FA verified for user: {current_user.email}")
        
        return Verify2FASetupResponse(
            success=True,
            message="Google Authenticator verified! You'll need to enter a code for subsequent decryptions."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to verify decrypt 2FA: {e}")
        raise HTTPException(status_code=500, detail="Verification failed")


@router.post("/verify-decrypt", response_model=VerifyDecryptTOTPResponse)
async def verify_totp_for_decrypt(
    request: VerifyDecryptTOTPRequest,
    current_user: UserDocument = Depends(get_current_user)
):
    """
    Verify TOTP code to access previously decrypted email.
    
    This is called when:
    - User has already decrypted the email once (using quantum keys)
    - User wants to view it again
    - User must enter Google Authenticator code to prove identity
    """
    try:
        if not current_user.totp_secret or not current_user.totp_verified:
            # TOTP not set up - allow access (first-time decryption flow handles this)
            return VerifyDecryptTOTPResponse(
                success=True,
                message="TOTP not required (not set up)"
            )
        
        # Verify TOTP code
        totp_secret = totp_service.decrypt_secret(current_user.totp_secret)
        code = request.code.replace(" ", "").strip()
        
        if len(code) != 6 or not code.isdigit():
            raise HTTPException(status_code=400, detail="Please enter a 6-digit code")
        
        is_valid = totp_service.verify_totp(totp_secret, code)
        
        if not is_valid:
            logger.warning(f"❌ Invalid TOTP for decrypt: {current_user.email}, email_id: {request.email_id}")
            raise HTTPException(status_code=401, detail="Invalid code. Please try again.")
        
        logger.info(f"✅ TOTP verified for decrypt: {current_user.email}, email_id: {request.email_id}")
        
        return VerifyDecryptTOTPResponse(
            success=True,
            message="Code verified! Loading decrypted content..."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TOTP verification failed: {e}")
        raise HTTPException(status_code=500, detail="Verification failed")


@router.delete("/disable")
async def disable_decrypt_2fa(
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Disable Google Authenticator for decrypt operations.
    After this, subsequent decrypts won't require TOTP.
    """
    try:
        await db.users.update_one(
            {"_id": current_user.id},
            {"$set": {
                "totp_secret": None,
                "totp_verified": False,
                "totp_enabled": False
            }}
        )
        
        logger.info(f"🔓 Decrypt 2FA disabled for user: {current_user.email}")
        
        return {"success": True, "message": "Google Authenticator disabled for decrypt operations."}
        
    except Exception as e:
        logger.error(f"Failed to disable decrypt 2FA: {e}")
        raise HTTPException(status_code=500, detail="Failed to disable")
