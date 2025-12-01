"""
Two-Factor Authentication (2FA) API Routes.
Implements TOTP-based 2FA compatible with Google Authenticator, Authy, Microsoft Authenticator.
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from motor.motor_asyncio import AsyncIOMotorDatabase
from passlib.hash import bcrypt
from datetime import datetime, timedelta
from typing import Optional
import secrets
import logging

from ..mongo_database import get_database
from ..mongo_models import UserDocument
from ..mongo_repositories import UserRepository
from ..services.totp_service import totp_service
from ..schemas.auth_schema import (
    RegisterRequest, RegisterResponse,
    LoginRequest, LoginResponse,
    Setup2FARequest, Setup2FAResponse,
    Verify2FASetupRequest, Verify2FASetupResponse,
    Verify2FALoginRequest, Verify2FALoginResponse,
    Disable2FARequest, Disable2FAResponse,
    RegenerateBackupCodesRequest, RegenerateBackupCodesResponse,
    TwoFactorStatusResponse
)
from .auth import get_current_user

router = APIRouter(prefix="/api/v1/auth/2fa", tags=["two-factor-auth"])
logger = logging.getLogger(__name__)

# Temporary tokens for 2FA verification (in-memory, use Redis in production)
_temp_tokens: dict = {}
TEMP_TOKEN_EXPIRY_MINUTES = 5


def _generate_temp_token() -> str:
    """Generate a temporary token for 2FA verification step."""
    return secrets.token_urlsafe(32)


def _store_temp_token(token: str, user_id: str, email: str):
    """Store temporary token for 2FA verification."""
    _temp_tokens[token] = {
        "user_id": user_id,
        "email": email,
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(minutes=TEMP_TOKEN_EXPIRY_MINUTES)
    }


def _validate_temp_token(token: str) -> Optional[dict]:
    """Validate and retrieve temporary token data."""
    if token not in _temp_tokens:
        return None
    
    data = _temp_tokens[token]
    if datetime.utcnow() > data["expires_at"]:
        del _temp_tokens[token]
        return None
    
    return data


def _consume_temp_token(token: str) -> Optional[dict]:
    """Validate, retrieve, and delete temporary token."""
    data = _validate_temp_token(token)
    if data:
        del _temp_tokens[token]
    return data


def _generate_session_token() -> str:
    """Generate a secure session token."""
    return secrets.token_urlsafe(64)


# ============================================
# Registration & Login Endpoints
# ============================================

@router.post("/register", response_model=RegisterResponse)
async def register_user(
    request: RegisterRequest,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Register a new user with email and password.
    After registration, user should set up 2FA.
    """
    try:
        user_repo = UserRepository(db)
        
        # Check if user already exists
        existing_user = await user_repo.find_by_email(request.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Hash password
        password_hash = bcrypt.hash(request.password)
        
        # Create user
        user_doc = UserDocument(
            email=request.email,
            display_name=request.display_name or request.email.split('@')[0],
            password_hash=password_hash,
            totp_enabled=False,
            totp_verified=False,
            created_at=datetime.utcnow()
        )
        
        user = await user_repo.create(user_doc)
        
        logger.info(f"New user registered: {request.email}")
        
        return RegisterResponse(
            user_id=str(user.id),
            email=user.email,
            message="Registration successful. Please set up two-factor authentication.",
            requires_2fa_setup=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")


@router.post("/login", response_model=LoginResponse)
async def login_user(
    request: LoginRequest,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Login with email and password.
    If 2FA is enabled, returns a temporary token for the second step.
    If 2FA is not enabled, returns a full session token.
    """
    try:
        user_repo = UserRepository(db)
        
        # Find user
        user = await user_repo.find_by_email(request.email)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Verify password
        if not user.password_hash or not bcrypt.verify(request.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Check if 2FA is enabled
        if user.totp_enabled and user.totp_verified:
            # Generate temporary token for 2FA step
            temp_token = _generate_temp_token()
            _store_temp_token(temp_token, str(user.id), user.email)
            
            logger.info(f"2FA required for user: {request.email}")
            
            return LoginResponse(
                user_id=str(user.id),
                email=user.email,
                requires_2fa=True,
                temp_token=temp_token
            )
        else:
            # No 2FA, generate full session
            session_token = _generate_session_token()
            expires_at = datetime.utcnow() + timedelta(hours=24)
            
            # Update user session
            await db.users.update_one(
                {"_id": user.id},
                {"$set": {
                    "session_token": session_token,
                    "last_login": datetime.utcnow()
                }}
            )
            
            logger.info(f"User logged in without 2FA: {request.email}")
            
            return LoginResponse(
                user_id=str(user.id),
                email=user.email,
                requires_2fa=False,
                session_token=session_token,
                expires_at=expires_at
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(status_code=500, detail="Login failed")


@router.post("/verify-login", response_model=Verify2FALoginResponse)
async def verify_2fa_login(
    request: Verify2FALoginRequest,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Complete login with 2FA code.
    Accepts either a 6-digit TOTP code or a backup code.
    """
    try:
        # Validate temporary token
        token_data = _consume_temp_token(request.temp_token)
        if not token_data:
            raise HTTPException(status_code=401, detail="Invalid or expired verification token")
        
        user_repo = UserRepository(db)
        user = await user_repo.find_by_email(token_data["email"])
        
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        # Get TOTP secret
        totp_secret = totp_service.decrypt_secret(user.totp_secret)
        
        # Clean code
        code = request.code.replace(" ", "").replace("-", "").strip()
        
        # Try TOTP verification first
        if len(code) == 6 and code.isdigit():
            is_valid = totp_service.verify_totp(totp_secret, code)
            
            if not is_valid:
                raise HTTPException(status_code=401, detail="Invalid verification code")
        else:
            # Try backup code
            backup_hashes = user.backup_codes or []
            used_hashes = user.backup_codes_used or []
            
            is_valid, code_hash = totp_service.verify_backup_code(request.code, backup_hashes, used_hashes)
            
            if not is_valid:
                raise HTTPException(status_code=401, detail="Invalid verification code")
            
            # Mark backup code as used
            await db.users.update_one(
                {"_id": user.id},
                {"$push": {"backup_codes_used": code_hash}}
            )
            logger.info(f"Backup code used for user: {user.email}")
        
        # Generate session token
        session_token = _generate_session_token()
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        # Update user session
        await db.users.update_one(
            {"_id": user.id},
            {"$set": {
                "session_token": session_token,
                "last_login": datetime.utcnow()
            }}
        )
        
        logger.info(f"2FA login successful: {user.email}")
        
        return Verify2FALoginResponse(
            success=True,
            user_email=user.email,
            session_token=session_token,
            expires_at=expires_at,
            message="Login successful"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"2FA verification failed: {e}")
        raise HTTPException(status_code=500, detail="Verification failed")


# ============================================
# 2FA Setup Endpoints
# ============================================

@router.post("/setup", response_model=Setup2FAResponse)
async def setup_2fa(
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Initialize 2FA setup for the current user.
    Returns QR code for Google Authenticator and backup codes.
    """
    try:
        if current_user.totp_enabled and current_user.totp_verified:
            raise HTTPException(status_code=400, detail="2FA is already enabled. Disable it first to reconfigure.")
        
        # Generate 2FA setup data
        setup_data = totp_service.setup_2fa(current_user.email)
        
        # Store encrypted secret and backup code hashes (not verified yet)
        await db.users.update_one(
            {"_id": current_user.id},
            {"$set": {
                "totp_secret": setup_data["secret"],
                "backup_codes": setup_data["backup_code_hashes"],
                "backup_codes_used": [],
                "totp_enabled": False,  # Not enabled until verified
                "totp_verified": False
            }}
        )
        
        logger.info(f"2FA setup initiated for user: {current_user.email}")
        
        return Setup2FAResponse(
            qr_code=setup_data["qr_code"],
            secret=setup_data["secret_plain"],  # For manual entry
            provisioning_uri=setup_data["provisioning_uri"],
            backup_codes=setup_data["backup_codes"],
            message="Scan the QR code with Google Authenticator, then verify with a code."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"2FA setup failed: {e}")
        raise HTTPException(status_code=500, detail="2FA setup failed")


@router.post("/verify-setup", response_model=Verify2FASetupResponse)
async def verify_2fa_setup(
    request: Verify2FASetupRequest,
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Verify 2FA setup with initial code from authenticator app.
    This completes the 2FA enrollment process.
    """
    try:
        if not current_user.totp_secret:
            raise HTTPException(status_code=400, detail="2FA setup not initiated. Call /setup first.")
        
        if current_user.totp_verified:
            raise HTTPException(status_code=400, detail="2FA is already verified and enabled.")
        
        # Decrypt and verify
        totp_secret = totp_service.decrypt_secret(current_user.totp_secret)
        is_valid = totp_service.verify_totp(totp_secret, request.code)
        
        if not is_valid:
            raise HTTPException(status_code=400, detail="Invalid verification code. Please try again.")
        
        # Enable 2FA
        await db.users.update_one(
            {"_id": current_user.id},
            {"$set": {
                "totp_enabled": True,
                "totp_verified": True
            }}
        )
        
        logger.info(f"2FA enabled for user: {current_user.email}")
        
        return Verify2FASetupResponse(
            success=True,
            message="Two-factor authentication has been enabled successfully.",
            totp_enabled=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"2FA verification failed: {e}")
        raise HTTPException(status_code=500, detail="Verification failed")


# ============================================
# 2FA Management Endpoints
# ============================================

@router.get("/status", response_model=TwoFactorStatusResponse)
async def get_2fa_status(
    current_user: UserDocument = Depends(get_current_user)
):
    """Get current 2FA status for the authenticated user."""
    backup_codes_total = len(current_user.backup_codes or [])
    backup_codes_used = len(current_user.backup_codes_used or [])
    
    return TwoFactorStatusResponse(
        enabled=current_user.totp_enabled,
        verified=current_user.totp_verified,
        backup_codes_remaining=backup_codes_total - backup_codes_used
    )


@router.post("/disable", response_model=Disable2FAResponse)
async def disable_2fa(
    request: Disable2FARequest,
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Disable 2FA for the current user.
    Requires current password and a valid TOTP code for security.
    """
    try:
        # Verify password
        if not current_user.password_hash or not bcrypt.verify(request.password, current_user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid password")
        
        # Verify TOTP code
        if not current_user.totp_secret:
            raise HTTPException(status_code=400, detail="2FA is not enabled")
        
        totp_secret = totp_service.decrypt_secret(current_user.totp_secret)
        is_valid = totp_service.verify_totp(totp_secret, request.code)
        
        if not is_valid:
            raise HTTPException(status_code=401, detail="Invalid verification code")
        
        # Disable 2FA
        await db.users.update_one(
            {"_id": current_user.id},
            {"$set": {
                "totp_secret": None,
                "totp_enabled": False,
                "totp_verified": False,
                "backup_codes": None,
                "backup_codes_used": None
            }}
        )
        
        logger.info(f"2FA disabled for user: {current_user.email}")
        
        return Disable2FAResponse(
            success=True,
            message="Two-factor authentication has been disabled."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to disable 2FA: {e}")
        raise HTTPException(status_code=500, detail="Failed to disable 2FA")


@router.post("/regenerate-backup-codes", response_model=RegenerateBackupCodesResponse)
async def regenerate_backup_codes(
    request: RegenerateBackupCodesRequest,
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Regenerate backup codes.
    Invalidates all previous backup codes.
    Requires a valid TOTP code for security.
    """
    try:
        if not current_user.totp_enabled:
            raise HTTPException(status_code=400, detail="2FA is not enabled")
        
        # Verify TOTP code
        totp_secret = totp_service.decrypt_secret(current_user.totp_secret)
        is_valid = totp_service.verify_totp(totp_secret, request.code)
        
        if not is_valid:
            raise HTTPException(status_code=401, detail="Invalid verification code")
        
        # Generate new backup codes
        backup_codes = totp_service.generate_backup_codes()
        backup_code_hashes = [totp_service.hash_backup_code(code) for code in backup_codes]
        
        # Update database
        await db.users.update_one(
            {"_id": current_user.id},
            {"$set": {
                "backup_codes": backup_code_hashes,
                "backup_codes_used": []
            }}
        )
        
        logger.info(f"Backup codes regenerated for user: {current_user.email}")
        
        return RegenerateBackupCodesResponse(
            backup_codes=backup_codes,
            message="New backup codes generated. Previous codes are now invalid."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to regenerate backup codes: {e}")
        raise HTTPException(status_code=500, detail="Failed to regenerate backup codes")
