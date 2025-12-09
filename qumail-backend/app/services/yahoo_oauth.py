"""
Yahoo OAuth Service for Yahoo Mail authentication
Uses Yahoo OAuth 2.0 and Yahoo Mail API

Note: Yahoo requires HTTPS redirect URIs, so we use:
- https://127.0.0.1:5173 for local development (with self-signed cert)
- Or use oob (out-of-band) flow with manual code entry
"""

import logging
import secrets
import aiohttp
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from urllib.parse import urlencode
from cryptography.fernet import Fernet
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class YahooOAuthError(Exception):
    """Yahoo OAuth related errors"""
    pass


class YahooTokenError(YahooOAuthError):
    """Yahoo token handling errors"""
    pass


class YahooOAuthService:
    """Yahoo OAuth service for Yahoo Mail"""
    
    # Yahoo OAuth 2.0 endpoints
    AUTH_ENDPOINT = "https://api.login.yahoo.com/oauth2/request_auth"
    TOKEN_ENDPOINT = "https://api.login.yahoo.com/oauth2/get_token"
    USER_INFO_ENDPOINT = "https://api.login.yahoo.com/openid/v1/userinfo"
    
    def __init__(self):
        self.client_id = getattr(settings, 'yahoo_client_id', '') or ''
        self.client_secret = getattr(settings, 'yahoo_client_secret', '') or ''
        
        # Yahoo requires HTTPS redirect URIs
        # For localhost, use 127.0.0.1 which Yahoo accepts with https
        self.redirect_uris = {
            "localhost": "https://127.0.0.1:5173/auth/yahoo/callback",
            "localhost_http": "http://localhost:5173/auth/yahoo/callback",  # May work for some apps
            "oob": "oob",  # Out-of-band (manual code entry)
            "netlify": "https://temp2mgm.netlify.app/auth/yahoo/callback",
            "vercel": "https://qumail-rho.vercel.app/auth/yahoo/callback",
        }
        
        # Default redirect URI - use HTTPS 127.0.0.1 for Yahoo
        self.redirect_uri = getattr(settings, 'yahoo_redirect_uri', '') or self.redirect_uris["localhost"]
        
        # Yahoo OAuth scopes
        # Yahoo uses different scope format
        self.scopes = [
            "openid",           # OpenID Connect
            "email",            # User email address
            "profile",          # User profile info
            "mail-r",           # Read mail (Yahoo-specific)
            "mail-w",           # Write/send mail (Yahoo-specific)
        ]
        
        # Initialize Fernet for token encryption
        try:
            self.fernet = Fernet(settings.encryption_master_key.encode())
        except Exception:
            self.fernet = None
            logger.warning("Token encryption not available for Yahoo OAuth")
        
        # OAuth state storage (use Redis in production)
        self._oauth_states: Dict[str, Dict[str, Any]] = {}
    
    def is_configured(self) -> bool:
        """Check if Yahoo OAuth is properly configured"""
        return bool(self.client_id and self.client_secret)
    
    def generate_authorization_url(
        self, 
        user_id: Optional[str] = None,
        redirect_uri_type: str = "localhost"
    ) -> Dict[str, str]:
        """
        Generate Yahoo OAuth authorization URL
        
        Args:
            user_id: Optional user ID for state tracking
            redirect_uri_type: Type of redirect URI to use
            
        Returns:
            Dict with authorization_url and state
        """
        if not self.is_configured():
            raise YahooOAuthError("Yahoo OAuth not configured")
        
        # Generate CSRF state token
        state = secrets.token_urlsafe(32)
        
        # Get redirect URI
        redirect_uri = self.redirect_uris.get(redirect_uri_type, self.redirect_uri)
        
        # Store state for verification
        self._oauth_states[state] = {
            "created_at": datetime.utcnow(),
            "user_id": user_id,
            "redirect_uri": redirect_uri
        }
        
        # Build authorization URL
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.scopes),
            "state": state,
            "language": "en-us",
        }
        
        authorization_url = f"{self.AUTH_ENDPOINT}?{urlencode(params)}"
        
        logger.info(f"Generated Yahoo OAuth URL with redirect: {redirect_uri}")
        
        return {
            "authorization_url": authorization_url,
            "state": state,
            "redirect_uri": redirect_uri
        }
    
    def verify_state(self, state: str) -> Optional[Dict[str, Any]]:
        """Verify OAuth state and return stored data"""
        if state not in self._oauth_states:
            logger.warning(f"Invalid OAuth state: {state}")
            return None
        
        state_data = self._oauth_states[state]
        
        # Check if state is expired (15 minutes)
        if datetime.utcnow() - state_data["created_at"] > timedelta(minutes=15):
            del self._oauth_states[state]
            logger.warning(f"Expired OAuth state: {state}")
            return None
        
        # Remove state after verification (single use)
        del self._oauth_states[state]
        
        return state_data
    
    async def exchange_code_for_tokens(
        self, 
        code: str, 
        redirect_uri: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Exchange authorization code for access and refresh tokens
        
        Args:
            code: Authorization code from Yahoo
            redirect_uri: Redirect URI used in authorization (must match)
            
        Returns:
            Dict with access_token, refresh_token, expires_in, etc.
        """
        if not self.is_configured():
            raise YahooOAuthError("Yahoo OAuth not configured")
        
        redirect_uri = redirect_uri or self.redirect_uri
        
        # Yahoo uses HTTP Basic Auth for token exchange
        import base64
        credentials = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {credentials}"
        }
        
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.TOKEN_ENDPOINT, 
                    data=data, 
                    headers=headers
                ) as response:
                    result = await response.json()
                    
                    if response.status != 200:
                        error = result.get("error", "unknown_error")
                        error_description = result.get("error_description", "Token exchange failed")
                        logger.error(f"Yahoo token exchange failed: {error} - {error_description}")
                        raise YahooTokenError(f"{error}: {error_description}")
                    
                    logger.info("Successfully exchanged Yahoo authorization code for tokens")
                    
                    return {
                        "access_token": result.get("access_token"),
                        "refresh_token": result.get("refresh_token"),
                        "token_type": result.get("token_type", "Bearer"),
                        "expires_in": result.get("expires_in", 3600),
                        "id_token": result.get("id_token"),
                        "xoauth_yahoo_guid": result.get("xoauth_yahoo_guid"),
                    }
                    
        except aiohttp.ClientError as e:
            logger.error(f"Network error during Yahoo token exchange: {e}")
            raise YahooOAuthError(f"Network error: {e}")
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh Yahoo access token using refresh token
        
        Args:
            refresh_token: The refresh token to use
            
        Returns:
            Dict with new access_token, refresh_token, etc.
        """
        if not self.is_configured():
            raise YahooOAuthError("Yahoo OAuth not configured")
        
        import base64
        credentials = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {credentials}"
        }
        
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.TOKEN_ENDPOINT, 
                    data=data, 
                    headers=headers
                ) as response:
                    result = await response.json()
                    
                    if response.status != 200:
                        error = result.get("error", "unknown_error")
                        error_description = result.get("error_description", "Token refresh failed")
                        logger.error(f"Yahoo token refresh failed: {error} - {error_description}")
                        raise YahooTokenError(f"{error}: {error_description}")
                    
                    logger.info("Successfully refreshed Yahoo access token")
                    
                    return {
                        "access_token": result.get("access_token"),
                        "refresh_token": result.get("refresh_token", refresh_token),
                        "token_type": result.get("token_type", "Bearer"),
                        "expires_in": result.get("expires_in", 3600),
                    }
                    
        except aiohttp.ClientError as e:
            logger.error(f"Network error during Yahoo token refresh: {e}")
            raise YahooOAuthError(f"Network error: {e}")
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        Get Yahoo user information using access token
        
        Args:
            access_token: Valid Yahoo access token
            
        Returns:
            Dict with user email, name, etc.
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.USER_INFO_ENDPOINT, 
                    headers=headers
                ) as response:
                    result = await response.json()
                    
                    if response.status != 200:
                        error = result.get("error", "unknown_error")
                        logger.error(f"Yahoo user info failed: {error}")
                        raise YahooOAuthError(f"Failed to get user info: {error}")
                    
                    logger.info(f"Retrieved Yahoo user info for: {result.get('email', 'unknown')}")
                    
                    return {
                        "sub": result.get("sub"),  # Yahoo user ID
                        "email": result.get("email"),
                        "email_verified": result.get("email_verified", False),
                        "name": result.get("name"),
                        "given_name": result.get("given_name"),
                        "family_name": result.get("family_name"),
                        "picture": result.get("picture"),
                        "locale": result.get("locale"),
                    }
                    
        except aiohttp.ClientError as e:
            logger.error(f"Network error getting Yahoo user info: {e}")
            raise YahooOAuthError(f"Network error: {e}")
    
    def encrypt_token(self, token: str) -> str:
        """Encrypt a token for secure storage"""
        if self.fernet:
            return self.fernet.encrypt(token.encode()).decode()
        return token
    
    def decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt a stored token"""
        if self.fernet:
            return self.fernet.decrypt(encrypted_token.encode()).decode()
        return encrypted_token
    
    async def revoke_token(self, access_token: str) -> bool:
        """
        Revoke Yahoo access token
        
        Note: Yahoo doesn't have a standard revoke endpoint,
        tokens expire automatically
        """
        logger.info("Yahoo token revocation requested (tokens expire automatically)")
        return True
    
    async def get_valid_token(self, user_id: str) -> Optional[str]:
        """
        Get a valid access token for the user, refreshing if needed
        
        Args:
            user_id: The user's ID
            
        Returns:
            Valid access token or None if unable to get one
        """
        from ..mongo_database import get_database
        
        try:
            db = await get_database()
            user = await db.users.find_one({"_id": user_id})
            
            if not user or not user.get("yahoo_tokens"):
                logger.warning(f"No Yahoo tokens found for user {user_id}")
                return None
            
            tokens = user["yahoo_tokens"]
            access_token = tokens.get("access_token")
            refresh_token = tokens.get("refresh_token")
            expires_at = tokens.get("expires_at")
            
            if not access_token:
                logger.warning(f"No access token in Yahoo tokens for user {user_id}")
                return None
            
            # Decrypt tokens if encrypted
            try:
                access_token = self.decrypt_token(access_token)
                if refresh_token:
                    refresh_token = self.decrypt_token(refresh_token)
            except Exception:
                pass  # Token may not be encrypted
            
            # Check if token is expired
            if expires_at:
                if isinstance(expires_at, str):
                    expires_at = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
                
                # Refresh if token expires in less than 5 minutes
                if datetime.utcnow() >= expires_at - timedelta(minutes=5):
                    if refresh_token:
                        logger.info(f"Refreshing expired Yahoo token for user {user_id}")
                        try:
                            new_tokens = await self.refresh_access_token(refresh_token)
                            
                            # Update stored tokens
                            await self.save_tokens(user_id, new_tokens)
                            
                            return new_tokens.get("access_token")
                        except Exception as e:
                            logger.error(f"Failed to refresh Yahoo token: {e}")
                            return None
                    else:
                        logger.warning(f"Yahoo token expired and no refresh token available for user {user_id}")
                        return None
            
            return access_token
            
        except Exception as e:
            logger.error(f"Error getting valid Yahoo token for user {user_id}: {e}")
            return None
    
    async def save_tokens(
        self, 
        user_id: str, 
        tokens: Dict[str, Any],
        user_email: Optional[str] = None
    ) -> bool:
        """
        Save Yahoo OAuth tokens to the user document
        
        Args:
            user_id: The user's ID
            tokens: Token dict with access_token, refresh_token, expires_in
            user_email: Optional Yahoo email address
            
        Returns:
            True if saved successfully
        """
        from ..mongo_database import get_database
        
        try:
            db = await get_database()
            
            # Calculate expiration time
            expires_in = tokens.get("expires_in", 3600)
            expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            
            # Encrypt tokens
            access_token = tokens.get("access_token", "")
            refresh_token = tokens.get("refresh_token", "")
            
            encrypted_access = self.encrypt_token(access_token) if access_token else ""
            encrypted_refresh = self.encrypt_token(refresh_token) if refresh_token else ""
            
            yahoo_tokens = {
                "access_token": encrypted_access,
                "refresh_token": encrypted_refresh,
                "expires_at": expires_at.isoformat(),
                "token_type": tokens.get("token_type", "Bearer"),
                "email": user_email,
                "yahoo_guid": tokens.get("xoauth_yahoo_guid"),
            }
            
            # Update user document
            result = await db.users.update_one(
                {"_id": user_id},
                {"$set": {"yahoo_tokens": yahoo_tokens}}
            )
            
            if result.modified_count > 0:
                logger.info(f"Saved Yahoo tokens for user {user_id}")
                return True
            else:
                logger.warning(f"No user found to update Yahoo tokens: {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error saving Yahoo tokens: {e}")
            return False
    
    async def clear_tokens(self, user_id: str) -> bool:
        """
        Clear Yahoo OAuth tokens from user document
        
        Args:
            user_id: The user's ID
            
        Returns:
            True if cleared successfully
        """
        from ..mongo_database import get_database
        
        try:
            db = await get_database()
            
            result = await db.users.update_one(
                {"_id": user_id},
                {"$unset": {"yahoo_tokens": ""}}
            )
            
            if result.modified_count > 0:
                logger.info(f"Cleared Yahoo tokens for user {user_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error clearing Yahoo tokens: {e}")
            return False


# Global service instance
yahoo_oauth_service = YahooOAuthService()
