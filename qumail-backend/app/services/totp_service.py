"""
TOTP (Time-Based One-Time Password) Service for Google Authenticator compatibility.
Implements RFC 6238 TOTP standard for two-factor authentication.
"""
import pyotp
import qrcode
import base64
import secrets
import hashlib
import logging
from io import BytesIO
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)

# Application name shown in authenticator apps
APP_NAME = "QuMail"
# TOTP settings (RFC 6238 standard)
TOTP_DIGITS = 6  # 6-digit codes
TOTP_INTERVAL = 30  # 30-second refresh
TOTP_ALGORITHM = "SHA1"  # Standard for Google Authenticator compatibility
# Backup codes
BACKUP_CODE_COUNT = 10
BACKUP_CODE_LENGTH = 8


class TOTPService:
    """
    TOTP service for two-factor authentication.
    Compatible with Google Authenticator, Authy, Microsoft Authenticator, and other TOTP apps.
    """
    
    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize TOTP service with optional encryption key for secret storage.
        
        Args:
            encryption_key: Base64-encoded encryption key for storing secrets.
                          If not provided, secrets will be stored as-is.
        """
        self._fernet = None
        if encryption_key:
            try:
                self._fernet = Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)
            except Exception as e:
                logger.warning(f"Failed to initialize Fernet encryption: {e}")
    
    def generate_secret(self) -> str:
        """
        Generate a new TOTP secret (base32 encoded).
        This secret will be shared with the user's authenticator app.
        
        Returns:
            Base32-encoded secret string
        """
        # Generate a 160-bit (20 byte) secret as per RFC 4226
        secret = pyotp.random_base32(length=32)
        logger.info("Generated new TOTP secret")
        return secret
    
    def encrypt_secret(self, secret: str) -> str:
        """
        Encrypt a TOTP secret for secure storage.
        
        Args:
            secret: Plain TOTP secret
            
        Returns:
            Encrypted secret (or original if encryption not available)
        """
        if self._fernet:
            try:
                return self._fernet.encrypt(secret.encode()).decode()
            except Exception as e:
                logger.warning(f"Failed to encrypt TOTP secret: {e}")
        return secret
    
    def decrypt_secret(self, encrypted_secret: str) -> str:
        """
        Decrypt a stored TOTP secret.
        
        Args:
            encrypted_secret: Encrypted TOTP secret
            
        Returns:
            Decrypted secret (or original if decryption not needed/failed)
        """
        if self._fernet:
            try:
                return self._fernet.decrypt(encrypted_secret.encode()).decode()
            except Exception as e:
                logger.warning(f"Failed to decrypt TOTP secret: {e}")
        return encrypted_secret
    
    def generate_provisioning_uri(self, secret: str, user_email: str) -> str:
        """
        Generate the provisioning URI for QR code.
        This URI follows the otpauth:// format that authenticator apps understand.
        
        Args:
            secret: TOTP secret (base32 encoded)
            user_email: User's email address (used as account name)
            
        Returns:
            otpauth:// URI string
        """
        totp = pyotp.TOTP(secret, digits=TOTP_DIGITS, interval=TOTP_INTERVAL)
        uri = totp.provisioning_uri(name=user_email, issuer_name=APP_NAME)
        logger.info(f"Generated provisioning URI for {user_email}")
        return uri
    
    def generate_qr_code(self, secret: str, user_email: str) -> str:
        """
        Generate a QR code image for the authenticator app to scan.
        
        Args:
            secret: TOTP secret (base32 encoded)
            user_email: User's email address
            
        Returns:
            Base64-encoded PNG image of the QR code
        """
        uri = self.generate_provisioning_uri(secret, user_email)
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(uri)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        logger.info(f"Generated QR code for {user_email}")
        return f"data:image/png;base64,{img_base64}"
    
    def verify_totp(self, secret: str, code: str, window: int = 1) -> bool:
        """
        Verify a TOTP code against the secret.
        
        Args:
            secret: TOTP secret (base32 encoded)
            code: 6-digit code from authenticator app
            window: Number of 30-second windows to check (for clock drift)
            
        Returns:
            True if code is valid, False otherwise
        """
        try:
            # Clean the code (remove spaces)
            code = code.replace(" ", "").strip()
            
            if len(code) != TOTP_DIGITS:
                logger.warning(f"Invalid TOTP code length: {len(code)}")
                return False
            
            totp = pyotp.TOTP(secret, digits=TOTP_DIGITS, interval=TOTP_INTERVAL)
            is_valid = totp.verify(code, valid_window=window)
            
            if is_valid:
                logger.info("TOTP code verified successfully")
            else:
                logger.warning("TOTP code verification failed")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"TOTP verification error: {e}")
            return False
    
    def get_current_code(self, secret: str) -> str:
        """
        Get the current TOTP code (for testing/debugging).
        
        Args:
            secret: TOTP secret (base32 encoded)
            
        Returns:
            Current 6-digit TOTP code
        """
        totp = pyotp.TOTP(secret, digits=TOTP_DIGITS, interval=TOTP_INTERVAL)
        return totp.now()
    
    def get_time_remaining(self) -> int:
        """
        Get seconds remaining until the current code expires.
        
        Returns:
            Seconds remaining (0-30)
        """
        return TOTP_INTERVAL - (int(datetime.utcnow().timestamp()) % TOTP_INTERVAL)
    
    def generate_backup_codes(self) -> List[str]:
        """
        Generate single-use backup codes for account recovery.
        Users should save these securely in case they lose access to their authenticator.
        
        Returns:
            List of 10 backup codes (8 characters each)
        """
        codes = []
        for _ in range(BACKUP_CODE_COUNT):
            # Generate a secure random code
            code = secrets.token_hex(BACKUP_CODE_LENGTH // 2).upper()
            # Format as XXXX-XXXX for readability
            formatted_code = f"{code[:4]}-{code[4:]}"
            codes.append(formatted_code)
        
        logger.info(f"Generated {BACKUP_CODE_COUNT} backup codes")
        return codes
    
    def hash_backup_code(self, code: str) -> str:
        """
        Hash a backup code for secure storage.
        
        Args:
            code: Plain backup code
            
        Returns:
            SHA-256 hash of the code
        """
        # Normalize the code (remove dashes, uppercase)
        normalized = code.replace("-", "").upper()
        return hashlib.sha256(normalized.encode()).hexdigest()
    
    def verify_backup_code(self, code: str, stored_hashes: List[str], used_hashes: List[str]) -> Tuple[bool, Optional[str]]:
        """
        Verify a backup code against stored hashes.
        
        Args:
            code: Backup code to verify
            stored_hashes: List of hashed backup codes
            used_hashes: List of already-used code hashes
            
        Returns:
            Tuple of (is_valid, code_hash_if_valid)
        """
        code_hash = self.hash_backup_code(code)
        
        if code_hash in used_hashes:
            logger.warning("Backup code already used")
            return False, None
        
        if code_hash in stored_hashes:
            logger.info("Backup code verified successfully")
            return True, code_hash
        
        logger.warning("Invalid backup code")
        return False, None
    
    def setup_2fa(self, user_email: str) -> Dict[str, Any]:
        """
        Complete 2FA setup flow: generate secret, QR code, and backup codes.
        
        Args:
            user_email: User's email address
            
        Returns:
            Dict containing secret, QR code, backup codes, and provisioning URI
        """
        # Generate new secret
        secret = self.generate_secret()
        
        # Generate QR code
        qr_code = self.generate_qr_code(secret, user_email)
        
        # Generate provisioning URI (for manual entry)
        provisioning_uri = self.generate_provisioning_uri(secret, user_email)
        
        # Generate backup codes
        backup_codes = self.generate_backup_codes()
        
        # Hash backup codes for storage
        backup_code_hashes = [self.hash_backup_code(code) for code in backup_codes]
        
        # Encrypt secret for storage
        encrypted_secret = self.encrypt_secret(secret)
        
        return {
            "secret": encrypted_secret,  # Store this in database
            "secret_plain": secret,  # Show to user for manual entry (don't store)
            "qr_code": qr_code,  # Base64 PNG image
            "provisioning_uri": provisioning_uri,  # otpauth:// URI
            "backup_codes": backup_codes,  # Show to user (don't store plain)
            "backup_code_hashes": backup_code_hashes,  # Store these in database
            "totp_digits": TOTP_DIGITS,
            "totp_interval": TOTP_INTERVAL,
            "app_name": APP_NAME
        }


# Global instance
totp_service = TOTPService()
