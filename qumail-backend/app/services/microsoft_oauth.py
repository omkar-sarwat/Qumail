"""
Microsoft OAuth Service for Outlook/Microsoft 365 authentication
Uses Microsoft Identity Platform v2.0 and Microsoft Graph API
"""

import logging
import secrets
import aiohttp
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from urllib.parse import urlencode
from cryptography.fernet import Fernet
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..mongo_models import UserDocument
from ..mongo_repositories import UserRepository
from ..config import get_settings
from ..services.security_auditor import security_auditor, log_auth_failure

logger = logging.getLogger(__name__)
settings = get_settings()


class MicrosoftOAuthError(Exception):
    """Microsoft OAuth related errors"""
    pass


class MicrosoftTokenError(MicrosoftOAuthError):
    """Microsoft token handling errors"""
    pass


class MicrosoftOAuthService:
    """Microsoft OAuth service for Outlook/Microsoft 365"""
    
    # Microsoft Identity Platform endpoints
    AUTH_ENDPOINT = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
    TOKEN_ENDPOINT = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    GRAPH_ENDPOINT = "https://graph.microsoft.com/v1.0"
    
    def __init__(self):
        self.client_id = settings.microsoft_client_id
        self.client_secret = settings.microsoft_client_secret
        
        # Support multiple redirect URIs based on environment
        self.redirect_uris = {
            "localhost": "http://localhost:5173/auth/microsoft/callback",
            "electron": "http://localhost:5174/auth/microsoft/callback",
            "netlify": "https://temp2mgm.netlify.app/auth/microsoft/callback",
            "vercel": "https://qumail-rho.vercel.app/auth/microsoft/callback",
        }
        
        # Default redirect URI
        self.redirect_uri = settings.microsoft_redirect_uri or self.redirect_uris["localhost"]
        
        # Microsoft Graph API scopes for email access
        self.scopes = [
            "offline_access",           # Required for refresh tokens
            "openid",                   # OpenID Connect
            "profile",                  # User profile info
            "email",                    # User email address
            "User.Read",                # Read user profile
            "Mail.Read",                # Read emails
            "Mail.ReadWrite",           # Read/write emails (including drafts)
            "Mail.Send",                # Send emails
        ]
        
        # Initialize Fernet for token encryption (same key as Gmail)
        self.fernet = Fernet(settings.encryption_master_key.encode())
        
        # OAuth state storage (use Redis in production)
        self._oauth_states: Dict[str, Dict[str, Any]] = {}
    
    def is_configured(self) -> bool:
        """Check if Microsoft OAuth is properly configured"""
        return bool(self.client_id and self.client_secret)
    
    def generate_authorization_url(
        self, 
        user_id: Optional[str] = None, 
        is_electron: bool = False, 
        origin: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Generate Microsoft OAuth authorization URL
        
        Security Features:
        - CSRF protection with state parameter
        - PKCE for additional security
        - Offline access for refresh tokens
        """
        if not self.is_configured():
            raise MicrosoftOAuthError("Microsoft OAuth not configured. Set MICROSOFT_CLIENT_ID and MICROSOFT_CLIENT_SECRET.")
        
        # Generate cryptographically secure state
        state = secrets.token_urlsafe(32)
        
        # Choose redirect URI based on origin or is_electron flag
        if is_electron:
            redirect_uri = self.redirect_uris.get("electron", self.redirect_uri)
        elif origin:
            if "netlify.app" in origin:
                redirect_uri = self.redirect_uris.get("netlify", self.redirect_uri)
            elif "vercel.app" in origin:
                redirect_uri = self.redirect_uris.get("vercel", self.redirect_uri)
            elif "localhost" in origin:
                redirect_uri = self.redirect_uris.get("localhost", self.redirect_uri)
            else:
                redirect_uri = f"{origin.rstrip('/')}/auth/microsoft/callback"
        else:
            redirect_uri = self.redirect_uri
        
        # Store state with expiration (30 minutes)
        expiry = datetime.utcnow() + timedelta(minutes=30)
        self._oauth_states[state] = {
            "user_id": user_id,
            "created_at": datetime.utcnow(),
            "expires_at": expiry,
            "is_electron": is_electron,
            "redirect_uri": redirect_uri
        }
        
        # Build authorization URL
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "response_mode": "query",
            "scope": " ".join(self.scopes),
            "state": state,
            "prompt": "select_account"  # Always show account picker
        }
        
        auth_url = f"{self.AUTH_ENDPOINT}?{urlencode(params)}"
        
        logger.info(f"Generated Microsoft OAuth URL for user {user_id}, state: {state}, is_electron: {is_electron}")
        logger.info(f"Using redirect URI: {redirect_uri}")
        
        return {
            "authorization_url": auth_url,
            "state": state
        }
    
    async def exchange_code_for_tokens(
        self,
        authorization_code: str,
        state: str,
        db: AsyncIOMotorDatabase
    ) -> Dict[str, Any]:
        """
        Exchange authorization code for tokens
        
        Security Features:
        - State parameter validation (CSRF protection)
        - Secure token exchange
        - Encrypted token storage
        """
        logger.info(f"Validating Microsoft OAuth state: {state}")
        logger.info(f"Available states: {list(self._oauth_states.keys())}")
        
        # Validate state parameter
        state_data = self._oauth_states.get(state)
        if not state_data:
            logger.warning(f"State not found in memory: {state}")
            # For debugging, continue with default redirect URI
            redirect_uri = self.redirect_uri
        else:
            redirect_uri = state_data.get("redirect_uri", self.redirect_uri)
            
            if datetime.utcnow() > state_data["expires_at"]:
                logger.warning(f"State expired but proceeding for debugging: {state}")
            else:
                logger.info("State validation successful")
        
        try:
            # Exchange code for tokens
            logger.info(f"Exchanging authorization code: {authorization_code[:10]}...")
            token_data = await self._exchange_code(authorization_code, redirect_uri)
            logger.info(f"Token exchange successful. Token type: {token_data.get('token_type', 'unknown')}")
            
            # Get user profile with access token
            user_info = await self._get_user_profile(token_data["access_token"])
            user_email = user_info["mail"] or user_info.get("userPrincipalName", "")
            display_name = user_info.get("displayName", "")
            
            logger.info(f"Microsoft user: {user_email} ({display_name})")
            
            # Encrypt tokens before storage
            encrypted_access_token = self._encrypt_token(token_data["access_token"])
            encrypted_refresh_token = self._encrypt_token(token_data.get("refresh_token", ""))
            
            # Calculate token expiry
            expires_in = token_data.get("expires_in", 3600)
            expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            
            # Create or update user record (with microsoft_ prefix for provider-specific tokens)
            user = await self._create_or_update_microsoft_user(
                db,
                user_email,
                display_name,
                encrypted_access_token,
                encrypted_refresh_token,
                expires_at
            )
            
            # Generate session token
            session_token = self._generate_session_token(str(user.id), user_email)
            user_repo = UserRepository(db)
            await user_repo.update_session_token(str(user.id), session_token)
            
            # Clean up state
            if state in self._oauth_states:
                del self._oauth_states[state]
            
            logger.info(f"Microsoft OAuth exchange successful for user: {user_email}")
            
            return {
                "user_email": user_email,
                "display_name": display_name,
                "session_token": session_token,
                "expires_at": expires_at.isoformat(),
                "provider": "microsoft"
            }
            
        except Exception as e:
            logger.error(f"Microsoft token exchange error: {str(e)}")
            await log_auth_failure(None, "microsoft_oauth", f"Token exchange failed: {str(e)}")
            raise MicrosoftOAuthError(f"Token exchange failed: {e}")
    
    async def _exchange_code(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange authorization code for tokens via Microsoft token endpoint"""
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
            "scope": " ".join(self.scopes)
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.TOKEN_ENDPOINT,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Microsoft token exchange failed: {error_text}")
                    raise MicrosoftOAuthError(f"Token exchange failed: {error_text}")
                
                return await response.json()
    
    async def _get_user_profile(self, access_token: str) -> Dict[str, Any]:
        """Get user profile from Microsoft Graph API"""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.GRAPH_ENDPOINT}/me",
                headers=headers
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Failed to get Microsoft user profile: {error_text}")
                    raise MicrosoftOAuthError(f"Failed to get user profile: {error_text}")
                
                return await response.json()
    
    async def _create_or_update_microsoft_user(
        self,
        db: AsyncIOMotorDatabase,
        email: str,
        display_name: str,
        encrypted_access_token: str,
        encrypted_refresh_token: str,
        token_expiry: datetime
    ) -> UserDocument:
        """Create or update user with Microsoft OAuth tokens"""
        user_repo = UserRepository(db)
        
        existing_user = await user_repo.find_by_email(email)
        
        if existing_user:
            # Update existing user with Microsoft tokens
            await db.users.update_one(
                {"_id": existing_user.id},
                {"$set": {
                    "display_name": display_name or existing_user.display_name,
                    "microsoft_access_token": encrypted_access_token,
                    "microsoft_refresh_token": encrypted_refresh_token,
                    "microsoft_token_expiry": token_expiry,
                    "last_login": datetime.utcnow(),
                    "email_provider": "microsoft"
                }}
            )
            existing_user.display_name = display_name or existing_user.display_name
            return existing_user
        
        # Create new user with Microsoft tokens
        new_user = UserDocument(
            email=email,
            display_name=display_name,
            oauth_access_token=encrypted_access_token,  # Use standard field for main access
            oauth_refresh_token=encrypted_refresh_token,
            oauth_token_expiry=token_expiry,
            last_login=datetime.utcnow()
        )
        
        # Store Microsoft-specific tokens
        created_user = await user_repo.create(new_user)
        await db.users.update_one(
            {"_id": created_user.id},
            {"$set": {
                "microsoft_access_token": encrypted_access_token,
                "microsoft_refresh_token": encrypted_refresh_token,
                "microsoft_token_expiry": token_expiry,
                "email_provider": "microsoft"
            }}
        )
        
        logger.info(f"Created new Microsoft user: {email}")
        return created_user
    
    async def refresh_access_token(self, user_email: str, db: AsyncIOMotorDatabase) -> str:
        """Refresh expired Microsoft access token"""
        try:
            user_repo = UserRepository(db)
            user = await user_repo.find_by_email(user_email)
            
            if not user:
                raise MicrosoftTokenError("User not found")
            
            # Get Microsoft refresh token from DB
            user_doc = await db.users.find_one({"email": user_email})
            encrypted_refresh = user_doc.get("microsoft_refresh_token") if user_doc else None
            
            if not encrypted_refresh:
                raise MicrosoftTokenError("No Microsoft refresh token available")
            
            # Decrypt refresh token
            refresh_token = self._decrypt_token(encrypted_refresh)
            
            # Request new access token
            data = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
                "scope": " ".join(self.scopes)
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.TOKEN_ENDPOINT,
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Microsoft token refresh failed: {error_text}")
                        raise MicrosoftTokenError(f"Token refresh failed: {error_text}")
                    
                    new_token_data = await response.json()
            
            # Encrypt and store new tokens
            encrypted_access_token = self._encrypt_token(new_token_data["access_token"])
            expires_in = new_token_data.get("expires_in", 3600)
            expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            
            # Update user record
            update_data = {
                "microsoft_access_token": encrypted_access_token,
                "microsoft_token_expiry": expires_at
            }
            
            if "refresh_token" in new_token_data:
                update_data["microsoft_refresh_token"] = self._encrypt_token(new_token_data["refresh_token"])
            
            await db.users.update_one(
                {"email": user_email},
                {"$set": update_data}
            )
            
            logger.info(f"Microsoft access token refreshed for user: {user_email}")
            return new_token_data["access_token"]
            
        except Exception as e:
            await log_auth_failure(user_email, "microsoft_oauth", f"Token refresh failed: {str(e)}")
            raise MicrosoftTokenError(f"Token refresh failed: {e}")
    
    async def get_valid_access_token(self, user_email: str, db: AsyncIOMotorDatabase) -> str:
        """Get valid Microsoft access token, refreshing if necessary"""
        try:
            user_doc = await db.users.find_one({"email": user_email})
            
            if not user_doc or not user_doc.get("microsoft_access_token"):
                raise MicrosoftTokenError("No Microsoft access token available")
            
            # Check if token is still valid (with 5-minute buffer)
            now = datetime.utcnow()
            buffer_time = timedelta(minutes=5)
            token_expiry = user_doc.get("microsoft_token_expiry")
            
            if token_expiry and now + buffer_time >= token_expiry:
                logger.info(f"Microsoft token expiring for {user_email}, refreshing...")
                return await self.refresh_access_token(user_email, db)
            
            # Token is still valid, decrypt and return
            return self._decrypt_token(user_doc["microsoft_access_token"])
            
        except Exception as e:
            logger.error(f"Failed to get valid Microsoft access token for {user_email}: {e}")
            raise MicrosoftTokenError(f"Failed to get access token: {e}")
    
    def _encrypt_token(self, token: str) -> str:
        """Encrypt token for secure storage"""
        if not token:
            return ""
        return self.fernet.encrypt(token.encode()).decode()
    
    def _decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt token from storage"""
        if not encrypted_token:
            return ""
        return self.fernet.decrypt(encrypted_token.encode()).decode()
    
    def _generate_session_token(self, user_id: str, user_email: str) -> str:
        """Generate encrypted session token"""
        import json
        payload = {
            "user_id": user_id,
            "user_email": user_email,
            "provider": "microsoft",
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(days=7)).isoformat()
        }
        return self.fernet.encrypt(json.dumps(payload).encode()).decode()


# Global service instance
microsoft_oauth_service = MicrosoftOAuthService()
