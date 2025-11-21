"""
Enhanced KM Client that supports both real and mock KM servers
"""

import os
import ssl
import base64
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple
import httpx
import json
import sys
import asyncio

from ..config import get_settings
from .mock_km_server import get_mock_km1, get_mock_km2, MockKMServer

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
    """
    Enhanced Key Manager client supporting both real KM servers and mock KM servers
    """
    
    def __init__(self, base_url: str, sae_id: int, 
                 client_cert_path: Optional[str] = None,
                 client_key_path: Optional[str] = None,
                 ca_cert_path: Optional[str] = None,
                 use_mock: bool = False,
                 mock_km: Optional[MockKMServer] = None):
        """
        Initialize KM client with options for both real and mock servers
        
        Args:
            base_url: The base URL of the KM server
            sae_id: The ID of the local SAE
            client_cert_path: Path to client certificate PEM file (for real KM server)
            client_key_path: Path to client key PEM file (for real KM server)
            ca_cert_path: Path to CA certificate PEM file (for real KM server)
            use_mock: Whether to use the mock KM server
            mock_km: Mock KM server instance to use (if use_mock is True)
        """
        self.base_url = base_url.rstrip('/')
        self.sae_id = sae_id
        self._client: Optional[httpx.AsyncClient] = None
        self._ssl_context: Optional[ssl.SSLContext] = None
        
        # Real KM server authentication
        self.client_cert_path = Path(client_cert_path) if client_cert_path else None
        self.client_key_path = Path(client_key_path) if client_key_path else None
        self.ca_cert_path = Path(ca_cert_path) if ca_cert_path else None
        
        # Mock KM server settings
        self.use_mock = use_mock
        self.mock_km = mock_km
        
        if self.use_mock and not self.mock_km:
            raise ValueError("Mock KM server instance must be provided when use_mock is True")
            
        logger.info(f"Initialized KMClient for SAE {sae_id} with {'MOCK' if use_mock else 'REAL'} KM server")

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create authenticated HTTP client"""
        if self.use_mock:
            # For mock server, we don't need an HTTP client
            return None
            
        if self._client is None:
            if self._ssl_context is None:
                self._ssl_context = await self._setup_ssl_context()
            
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=30.0,
                verify=self._ssl_context,
                headers={
                    "User-Agent": "QuMail-SAE/1.0",
                    "Content-Type": "application/json"
                }
            )
        return self._client
    
    async def _setup_ssl_context(self) -> ssl.SSLContext:
        """Create SSL context with client certificate authentication"""
        try:
            ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            ssl_context.verify_mode = ssl.CERT_REQUIRED
            ssl_context.check_hostname = False  # KM uses localhost
            
            # Load CA certificate for server verification
            if self.ca_cert_path and self.ca_cert_path.exists():
                ssl_context.load_verify_locations(cafile=str(self.ca_cert_path))
            else:
                logger.warning(f"CA certificate not found: {self.ca_cert_path}, disabling verification")
                ssl_context.verify_mode = ssl.CERT_NONE
            
            # Load client certificate and key for mutual TLS
            if (self.client_cert_path and self.client_cert_path.exists() and 
                self.client_key_path and self.client_key_path.exists()):
                ssl_context.load_cert_chain(
                    certfile=str(self.client_cert_path),
                    keyfile=str(self.client_key_path)
                )
            else:
                raise AuthenticationError(f"Client certificate files not found")
                
            return ssl_context
            
        except Exception as e:
            raise AuthenticationError(f"Failed to setup SSL context: {e}")

    async def close(self):
        """Close client connection and cleanup"""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def check_key_status(self, slave_sae_id: int) -> Dict[str, Any]:
        """Check availability of quantum keys for given slave SAE"""
        try:
            if self.use_mock:
                # Use mock KM server
                return self.mock_km.get_key_status(slave_sae_id)
            
            # Use real KM server
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
        except Exception as e:
            raise KMConnectionError(f"Unexpected error: {e}")

    async def request_enc_keys(self, slave_sae_id: int, number: int = 1, size: int = 256) -> List[Dict[str, Any]]:
        """Request encryption keys from KM server"""
        try:
            # Check if sufficient keys are available first
            status = await self.check_key_status(slave_sae_id)
            available = status.get('stored_key_count', 0)
            
            if available < number:
                raise InsufficientKeysError(f"Insufficient keys: requested {number}, available {available}")
            
            max_size = status.get('max_key_size', 256)
            if size > max_size:
                raise InsufficientKeysError(f"Key size too large: requested {size}, max {max_size}")
            
            if self.use_mock:
                # Use mock KM server
                keys = self.mock_km.request_enc_keys(slave_sae_id, number)
                logger.info(f"Retrieved {len(keys)} encryption keys from mock KM for SAE {slave_sae_id}")
                return keys
            
            # Use real KM server
            client = await self._get_client()
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
        except InsufficientKeysError:
            raise
        except Exception as e:
            raise KMConnectionError(f"Unexpected error: {e}")

    async def request_dec_keys(self, master_sae_id: int, key_ids: List[str]) -> List[Dict[str, Any]]:
        """Request decryption keys using key IDs"""
        try:
            if self.use_mock:
                # Use mock KM server
                keys = self.mock_km.request_dec_keys(master_sae_id, key_ids)
                logger.info(f"Retrieved {len(keys)} decryption keys from mock KM from SAE {master_sae_id}")
                return keys
            
            # Use real KM server
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
        except Exception as e:
            raise KMConnectionError(f"Unexpected error: {e}")

    async def get_sae_info(self) -> Dict[str, Any]:
        """Get information about this SAE"""
        try:
            if self.use_mock:
                # Use mock KM server
                return self.mock_km.get_sae_info()
            
            # Use real KM server
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
        except Exception as e:
            raise KMConnectionError(f"Unexpected error: {e}")

    async def check_entropy(self) -> float:
        """Check total entropy of keys (security monitoring)"""
        try:
            if self.use_mock:
                # Use mock KM server
                entropy_info = self.mock_km.get_entropy()
                return entropy_info.get("total_entropy", 7.9)
            
            # Use real KM server
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
            if self.use_mock:
                # Use mock KM server
                return self.mock_km.mark_key_consumed(key_id)
            
            # Use real KM server
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
            if self.use_mock:
                # Use mock KM server
                return self.mock_km.get_status()
            
            # Use real KM server
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

# Create enhanced KM clients with mock support
def create_enhanced_km_clients(use_mock: bool = True) -> Tuple[KMClient, KMClient]:
    """Create enhanced KM clients with optional mock server support"""
    settings = get_settings()
    
    # Determine client certificate paths
    root_dir = Path(r"D:\New folder (8)\qumail-secure-email\qkd_kme_server-master\certs")
    
    # Alice's certificates (KME 1)
    km1_client_cert_path = str(root_dir / "kme-1-local-zone" / "client_1_cert.pem")
    km1_client_key_path = str(root_dir / "kme-1-local-zone" / "client_1.key")
    km1_ca_cert_path = str(root_dir / "kme-1-local-zone" / "ca.crt")
    
    # Bob's certificates (KME 2)
    km2_client_cert_path = str(root_dir / "kme-2-local-zone" / "client_3_cert.pem")
    km2_client_key_path = str(root_dir / "kme-2-local-zone" / "client_3.key")
    km2_ca_cert_path = str(root_dir / "kme-2-local-zone" / "ca.crt")
    
    # Create KM clients
    if use_mock:
        # Use mock KM servers
        mock_km1 = get_mock_km1()
        mock_km2 = get_mock_km2()
        
        km1_client = KMClient(
            base_url=settings.km1_base_url,
            sae_id=settings.sender_sae_id,
            use_mock=True,
            mock_km=mock_km1
        )
        
        km2_client = KMClient(
            base_url=settings.km2_base_url,
            sae_id=settings.receiver_sae_id,
            use_mock=True,
            mock_km=mock_km2
        )
    else:
        # Use real KM servers
        km1_client = KMClient(
            base_url=settings.km1_base_url,
            sae_id=settings.sender_sae_id,
            client_cert_path=km1_client_cert_path,
            client_key_path=km1_client_key_path,
            ca_cert_path=km1_ca_cert_path
        )
        
        km2_client = KMClient(
            base_url=settings.km2_base_url,
            sae_id=settings.receiver_sae_id,
            client_cert_path=km2_client_cert_path,
            client_key_path=km2_client_key_path,
            ca_cert_path=km2_ca_cert_path
        )
    
    return km1_client, km2_client

# Global client instances with mock KM servers
km1_client, km2_client = create_enhanced_km_clients(use_mock=True)

# Function to get the global instances
def get_km_clients():
    return km1_client, km2_client
