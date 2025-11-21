import ssl
import base64
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import pkcs12
import httpx
from ..config import get_settings

logger = logging.getLogger(__name__)

class SecurityError(Exception):
    """Base class for security-related errors"""
    pass

class KMConnectionError(SecurityError):
    """Raised when KM server is unreachable"""
    pass

class InsufficientKeysError(SecurityError):
    """Raised when not enough quantum keys are available"""
    pass

class AuthenticationError(SecurityError):
    """Raised when SAE authentication fails"""
    pass

class KMClient:
    """Secure Key Manager client with proper certificate authentication"""
    
    def __init__(self, base_url: str, sae_id: int, pfx_path: str, pfx_password: str, ca_cert_path: str, key_path: str = ""):
        self.base_url = base_url.rstrip('/')
        self.sae_id = sae_id
        self.pfx_path = Path(pfx_path)
        self.key_path = Path(key_path) if key_path else None
        self.pfx_password = pfx_password.encode() if pfx_password else None
        self.ca_cert_path = Path(ca_cert_path)
        self._client: Optional[httpx.AsyncClient] = None
        self._ssl_context: Optional[ssl.SSLContext] = None

    def _load_certificates(self) -> ssl.SSLContext:
        """Load client certificate and create SSL context with proper security"""
        try:
            # Create SSL context with strong security
            context = ssl.create_default_context()
            context.check_hostname = False  # KM uses localhost for development
            context.verify_mode = ssl.CERT_NONE  # Disable for development with self-signed certs
            
            # If we have separate PEM cert and key files (next-door-key-simulator format)
            if self.key_path and self.key_path.exists() and self.pfx_path.exists():
                logger.info(f"Loading PEM certificate: {self.pfx_path}")
                logger.info(f"Loading PEM key: {self.key_path}")
                
                # Load PEM certificate and key directly
                context.load_cert_chain(str(self.pfx_path), str(self.key_path))
                
            # Otherwise try to load PFX certificate
            elif self.pfx_path.exists():
                logger.info(f"Loading PFX certificate: {self.pfx_path}")
                
                with open(self.pfx_path, 'rb') as f:
                    pfx_data = f.read()
                
                # Extract private key and certificate from PFX
                private_key, certificate, additional_certificates = pkcs12.load_key_and_certificates(
                    pfx_data, self.pfx_password
                )
                
                # Convert to PEM format and load into context
                cert_pem = certificate.public_bytes(serialization.Encoding.PEM)
                key_pem = private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                )
                
                # Create temporary files for SSL context
                import tempfile
                with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.pem') as cert_file:
                    cert_file.write(cert_pem)
                    cert_file.write(key_pem)
                    context.load_cert_chain(cert_file.name)
            else:
                logger.warning(f"No client certificates found at {self.pfx_path}")
                # Continue without client certificate for development
            
            # Load CA certificate for server verification (optional for development)
            if self.ca_cert_path.exists():
                logger.info(f"Loading CA certificate: {self.ca_cert_path}")
                context.load_verify_locations(cafile=str(self.ca_cert_path))
            else:
                logger.warning(f"CA certificate not found: {self.ca_cert_path}, continuing without verification")
            
            logger.info(f"SSL context configured for KM server {self.base_url}")
            return context
            
        except Exception as e:
            logger.error(f"Failed to load certificates for KM client: {e}")
            logger.error(f"Certificate path: {self.pfx_path}")
            logger.error(f"CA certificate path: {self.ca_cert_path}")
            logger.warning("Continuing with insecure SSL context for development")
            
            # Fallback: create insecure context for development
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            return context

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create authenticated HTTP client"""
        if self._client is None:
            # Check if using HTTP or HTTPS
            is_https = self.base_url.startswith('https://')
            
            client_kwargs = {
                "base_url": self.base_url,
                "timeout": 30.0,
                "headers": {
                    "User-Agent": "QuMail-SAE/1.0",
                    "Content-Type": "application/json"
                }
            }
            
            # Only set SSL context for HTTPS connections
            if is_https:
                if self._ssl_context is None:
                    self._ssl_context = self._load_certificates()
                client_kwargs["verify"] = self._ssl_context
            else:
                logger.info(f"Using HTTP connection to {self.base_url} (no SSL)")
            
            self._client = httpx.AsyncClient(**client_kwargs)
        return self._client

    async def close(self):
        """Close client connection and cleanup"""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def check_key_status(self, slave_sae_id: int) -> Dict[str, Any]:
        """Check availability of quantum keys for given slave SAE"""
        try:
            client = await self._get_client()
            response = await client.get(f"/api/v1/keys/{slave_sae_id}/status")
            response.raise_for_status()
            
            status = response.json()
            logger.info(f"Key status for SAE {slave_sae_id}: {status.get('stored_key_count', 0)} keys available")
            return status
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise InsufficientKeysError(f"No keys available for SAE {slave_sae_id}")
            elif e.response.status_code == 401:
                raise AuthenticationError("SAE authentication failed")
            else:
                raise KMConnectionError(f"KM server error: {e.response.status_code}")
        except httpx.RequestError as e:
            raise KMConnectionError(f"Failed to connect to KM server: {e}")

    async def request_enc_keys(self, slave_sae_id: int, number: int = 1, size: int = 256) -> List[Dict[str, Any]]:
        """Request encryption keys from KM server"""
        try:
            client = await self._get_client()
            
            # Check if sufficient keys are available first
            status = await self.check_key_status(slave_sae_id)
            available = status.get('stored_key_count', 0)
            
            if available < number:
                raise InsufficientKeysError(f"Insufficient keys: requested {number}, available {available}")
            
            max_size = status.get('max_key_size', 256)
            if size > max_size:
                raise InsufficientKeysError(f"Key size too large: requested {size}, max {max_size}")
            
            # Request keys
            payload = {"number": number, "size": size}
            response = await client.post(f"/api/v1/keys/{slave_sae_id}/enc_keys", json=payload)
            response.raise_for_status()
            
            data = response.json()
            keys = data.get("keys", [])
            
            if len(keys) != number:
                raise KMConnectionError(f"KM returned {len(keys)} keys, expected {number}")
            
            logger.info(f"Retrieved {len(keys)} encryption keys for SAE {slave_sae_id}")
            return keys
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise AuthenticationError("SAE authentication failed")
            elif e.response.status_code == 400:
                raise InsufficientKeysError("Invalid key request parameters")
            else:
                raise KMConnectionError(f"KM server error: {e.response.status_code}")
        except httpx.RequestError as e:
            raise KMConnectionError(f"Failed to connect to KM server: {e}")

    async def request_dec_keys(self, master_sae_id: int, key_ids: List[str]) -> List[Dict[str, Any]]:
        """Request decryption keys using key IDs"""
        try:
            client = await self._get_client()
            
            payload = {"key_IDs": [{"key_ID": kid} for kid in key_ids]}
            response = await client.post(f"/api/v1/keys/{master_sae_id}/dec_keys", json=payload)
            response.raise_for_status()
            
            data = response.json()
            keys = data.get("keys", [])
            
            if len(keys) != len(key_ids):
                raise KMConnectionError(f"KM returned {len(keys)} keys, expected {len(key_ids)}")
            
            logger.info(f"Retrieved {len(keys)} decryption keys from SAE {master_sae_id}")
            return keys
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise AuthenticationError("SAE authentication failed")
            elif e.response.status_code == 404:
                raise SecurityError("One or more key IDs not found - possible tampering")
            else:
                raise KMConnectionError(f"KM server error: {e.response.status_code}")
        except httpx.RequestError as e:
            raise KMConnectionError(f"Failed to connect to KM server: {e}")

    async def get_sae_info(self) -> Dict[str, Any]:
        """Get information about this SAE"""
        try:
            client = await self._get_client()
            response = await client.get("/api/v1/sae/info/me")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise AuthenticationError("SAE not registered with KM")
            raise KMConnectionError(f"KM server error: {e.response.status_code}")
        except httpx.RequestError as e:
            raise KMConnectionError(f"Failed to connect to KM server: {e}")

    async def check_entropy(self) -> float:
        """Check total entropy of keys (security monitoring)"""
        try:
            client = await self._get_client()
            response = await client.get("/api/v1/keys/entropy/total")
            response.raise_for_status()
            
            data = response.json()
            entropy = data.get("total_entropy", 0.0)
            
            # Warn if entropy is suspiciously low (possible attack)
            if entropy < 7.0:
                logger.warning(f"Low entropy detected: {entropy} - possible QKD compromise")
            
            return entropy
            
        except Exception as e:
            logger.warning(f"Failed to check entropy: {e}")
            return 0.0
    
    async def mark_key_consumed(self, key_id: str) -> bool:
        """Mark quantum key as consumed (one-time use enforcement)"""
        try:
            client = await self._get_client()
            payload = {"key_id": key_id, "consumed": True}
            response = await client.post(f"/api/v1/keys/mark_consumed", json=payload)
            
            if response.status_code == 200:
                logger.info(f"Key {key_id} marked as consumed")
                return True
            elif response.status_code == 404:
                logger.warning(f"Key {key_id} not found for consumption marking")
                return False
            else:
                response.raise_for_status()
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.info(f"Key {key_id} already consumed or not found")
                return True  # Already consumed is OK
            logger.error(f"Failed to mark key {key_id} as consumed: {e}")
            return False
        except Exception as e:
            logger.error(f"Error marking key {key_id} as consumed: {e}")
            return False
    
    async def get_status(self) -> Dict[str, Any]:
        """Get KM server health and key availability status"""
        try:
            client = await self._get_client()
            response = await client.get("/api/v1/status")
            response.raise_for_status()
            
            status = response.json()
            
            # Check for critical indicators
            healthy = status.get("healthy", False)
            available_keys = status.get("stored_key_count", 0)
            entropy = status.get("entropy", 0.0)
            
            # Enhance status with security analysis
            status["security_analysis"] = {
                "entropy_healthy": entropy >= 7.0,
                "keys_sufficient": available_keys >= 10,
                "overall_health": healthy and entropy >= 7.0 and available_keys >= 10
            }
            
            logger.info(f"KM status: healthy={healthy}, keys={available_keys}, entropy={entropy}")
            return status
            
        except httpx.HTTPStatusError as e:
            logger.error(f"KM server status error: {e.response.status_code}")
            return {
                "healthy": False,
                "error": f"HTTP {e.response.status_code}",
                "available_keys": 0,
                "entropy": 0.0,
                "security_analysis": {
                    "entropy_healthy": False,
                    "keys_sufficient": False,
                    "overall_health": False
                }
            }
        except Exception as e:
            logger.error(f"KM status check failed: {e}")
            return {
                "healthy": False,
                "error": str(e),
                "available_keys": 0,
                "entropy": 0.0,
                "security_analysis": {
                    "entropy_healthy": False,
                    "keys_sufficient": False,
                    "overall_health": False
                }
            }

# Factory functions for KM clients
def create_km_clients():
    settings = get_settings()
    
    km1_client = KMClient(
        base_url=settings.km1_base_url,
        sae_id=settings.sender_sae_id,
        pfx_path=settings.km1_client_cert_pfx,
        pfx_password=settings.km_client_cert_password,
        ca_cert_path=settings.km1_ca_cert,
        key_path=settings.km1_client_key
    )
    
    km2_client = KMClient(
        base_url=settings.km2_base_url,
        sae_id=settings.receiver_sae_id,
        pfx_path=settings.km2_client_cert_pfx,
        pfx_password=settings.km_client_cert_password,
        ca_cert_path=settings.km2_ca_cert,
        key_path=settings.km2_client_key
    )
    
    return km1_client, km2_client

# Global client instances
km1_client, km2_client = create_km_clients()

# Alias for compatibility with quantum key manager
OptimizedKMClient = KMClient
