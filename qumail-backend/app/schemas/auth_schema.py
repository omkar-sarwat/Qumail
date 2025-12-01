from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List

class AuthStartResponse(BaseModel):
    authorization_url: str
    state: str

class AuthCallbackRequest(BaseModel):
    code: str
    state: str

class AuthCallbackResponse(BaseModel):
    user_email: EmailStr
    session_token: str
    expires_at: datetime

class TokenRefreshResponse(BaseModel):
    access_token: str
    expires_at: datetime

# ============================================
# TOTP 2FA Schemas
# ============================================

class RegisterRequest(BaseModel):
    """User registration request"""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    display_name: Optional[str] = None

class RegisterResponse(BaseModel):
    """User registration response"""
    user_id: str
    email: str
    message: str
    requires_2fa_setup: bool = True

class LoginRequest(BaseModel):
    """Initial login request (password only)"""
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    """Login response - may require 2FA"""
    user_id: str
    email: str
    requires_2fa: bool
    session_token: Optional[str] = None  # Only set if 2FA not enabled
    expires_at: Optional[datetime] = None
    temp_token: Optional[str] = None  # Temporary token for 2FA verification

class Setup2FARequest(BaseModel):
    """Request to initialize 2FA setup"""
    pass  # Uses current authenticated user

class Setup2FAResponse(BaseModel):
    """2FA setup response with QR code"""
    qr_code: str  # Base64 PNG image
    secret: str  # For manual entry
    provisioning_uri: str  # otpauth:// URI
    backup_codes: List[str]  # Single-use backup codes
    message: str

class Verify2FASetupRequest(BaseModel):
    """Verify 2FA setup with initial code"""
    code: str = Field(..., min_length=6, max_length=6, description="6-digit code from authenticator")

class Verify2FASetupResponse(BaseModel):
    """2FA setup verification response"""
    success: bool
    message: str
    totp_enabled: bool

class Verify2FALoginRequest(BaseModel):
    """2FA verification during login"""
    temp_token: str  # Temporary token from login step
    code: str = Field(..., min_length=6, max_length=8, description="6-digit TOTP code or backup code")

class Verify2FALoginResponse(BaseModel):
    """2FA login verification response"""
    success: bool
    user_email: str
    session_token: str
    expires_at: datetime
    message: str

class Disable2FARequest(BaseModel):
    """Request to disable 2FA"""
    password: str
    code: str = Field(..., description="Current TOTP code for verification")

class Disable2FAResponse(BaseModel):
    """2FA disable response"""
    success: bool
    message: str

class RegenerateBackupCodesRequest(BaseModel):
    """Request to regenerate backup codes"""
    code: str = Field(..., min_length=6, max_length=6, description="Current TOTP code")

class RegenerateBackupCodesResponse(BaseModel):
    """New backup codes response"""
    backup_codes: List[str]
    message: str

class TwoFactorStatusResponse(BaseModel):
    """Current 2FA status for user"""
    enabled: bool
    verified: bool
    backup_codes_remaining: int
