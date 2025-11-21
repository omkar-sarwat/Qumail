"""
Direct KM Client for communication with real quantum key management servers.
This client connects directly to the KM servers without any fallback mechanisms.
"""

import os
import ssl
import base64
import logging
import httpx
import asyncio
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class DirectKMClient:
    """Direct client for real KM servers without fallback"""
    
    def __init__(self, base_url: str, sae_id: int, 
                client_cert_path: str,
                client_key_path: str,
                ca_cert_path: str):
        """Initialize KM client with certificate paths"""
        self.base_url = base_url.rstrip('/')
        self.sae_id = sae_id
        
        # Certificate paths
        self.client_cert_path = Path(client_cert_path)
        self.client_key_path = Path(client_key_path)
        self.ca_cert_path = Path(ca_cert_path)
        
        # HTTP client
        self._client = None
        self._ssl_context = None
        
        logger.info(f"Initialized DirectKMClient for SAE {sae_id} at {base_url}")

    async def _setup_ssl_context(self) -> ssl.SSLContext:
        """Create SSL context with client certificate authentication"""
        ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        ssl_context.check_hostname = False  # KM uses localhost
        
        # Load CA certificate for server verification
        if self.ca_cert_path.exists():
            ssl_context.load_verify_locations(cafile=str(self.ca_cert_path))
        else:
            logger.warning(f"CA certificate not found: {self.ca_cert_path}")
            ssl_context.verify_mode = ssl.CERT_NONE
        
        # Load client certificate and key
        if (self.client_cert_path.exists() and self.client_key_path.exists()):
            ssl_context.load_cert_chain(
                certfile=str(self.client_cert_path),
                keyfile=str(self.client_key_path)
            )
        else:
            raise Exception(f"Client certificate files not found")
                
        return ssl_context

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with proper SSL context"""
        if self._client is None:
            if self._ssl_context is None:
                self._ssl_context = await self._setup_ssl_context()
            
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=60.0,  # Long timeout for slow KM operations
                verify=self._ssl_context
            )
        return self._client

    async def close(self):
        """Close client connection"""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def check_key_status(self, slave_sae_id: int) -> Dict[str, Any]:
        """Check availability of quantum keys"""
        client = await self._get_client()
        try:
            response = await client.get(f"/api/v1/keys/{slave_sae_id}/status")
            response.raise_for_status()
            
            status = response.json()
            logger.info(f"Key status for SAE {slave_sae_id}: {status.get('stored_key_count', 0)} keys available")
            return status
        except Exception as e:
            logger.error(f"Failed to check key status: {e}")
            raise

    async def request_enc_keys(self, slave_sae_id: int, number: int = 1) -> List[Dict[str, Any]]:
        """Request encryption keys from KM server"""
        client = await self._get_client()
        try:
            payload = {"number": number}
            response = await client.post(f"/api/v1/keys/{slave_sae_id}/enc_keys", json=payload)
            response.raise_for_status()
            
            data = response.json()
            keys = data.get("keys", [])
            
            if len(keys) < number:
                logger.warning(f"Requested {number} keys but only received {len(keys)}")
            
            logger.info(f"Successfully fetched {len(keys)} keys from server")
            return keys
        except Exception as e:
            logger.error(f"Failed to request encryption keys: {e}")
            raise

    async def request_dec_keys(self, master_sae_id: int, key_ids: List[str]) -> List[Dict[str, Any]]:
        """Request decryption keys using key IDs"""
        client = await self._get_client()
        try:
            payload = {"key_IDs": [{"key_ID": kid} for kid in key_ids]}
            response = await client.post(f"/api/v1/keys/{master_sae_id}/dec_keys", json=payload)
            response.raise_for_status()
            
            data = response.json()
            keys = data.get("keys", [])
            
            if len(keys) != len(key_ids):
                logger.warning(f"Requested {len(key_ids)} keys but only received {len(keys)}")
            
            logger.info(f"Retrieved {len(keys)} decryption keys")
            return keys
        except Exception as e:
            logger.error(f"Failed to request decryption keys: {e}")
            raise

    async def mark_key_consumed(self, key_id: str) -> bool:
        """Mark quantum key as consumed"""
        client = await self._get_client()
        try:
            payload = {"key_id": key_id, "consumed": True}
            response = await client.post(f"/api/v1/keys/mark_consumed", json=payload)
            response.raise_for_status()
            logger.info(f"Key {key_id} marked as consumed")
            return True
        except Exception as e:
            logger.error(f"Failed to mark key {key_id} as consumed: {e}")
            return False

    async def get_status(self) -> Dict[str, Any]:
        """Get KM server health and key availability status"""
        client = await self._get_client()
        try:
            # Try status endpoint first
            try:
                response = await client.get("/api/v1/status")
                response.raise_for_status()
            except:
                # Fall back to root status
                response = await client.get("/")
                response.raise_for_status()
                
            return response.json()
        except Exception as e:
            logger.error(f"KM status check failed: {e}")
            return {
                "healthy": False,
                "error": str(e),
                "available_keys": 0
            }

# Create Direct KM client instances
def create_direct_km_clients():
    """Create direct KM clients with real certificates"""
    # Path for certificates relative to this file
    root_dir = Path(r"D:\New folder (8)\qumail-secure-email\qkd_kme_server-master\certs")
    
    # KME 1 certificates (SAE 1 - Alice)
    km1_client_cert = str(root_dir / "kme-1-local-zone" / "client_1_cert.pem")
    km1_client_key = str(root_dir / "kme-1-local-zone" / "client_1.key")
    km1_ca_cert = str(root_dir / "kme-1-local-zone" / "ca.crt")
    
    # KME 2 certificates (SAE 3 - Bob)
    km2_client_cert = str(root_dir / "kme-2-local-zone" / "client_3_cert.pem")
    km2_client_key = str(root_dir / "kme-2-local-zone" / "client_3.key")
    km2_ca_cert = str(root_dir / "kme-2-local-zone" / "ca.crt")
    
    km1_client = DirectKMClient(
        base_url="https://localhost:13000",
        sae_id=1,
        client_cert_path=km1_client_cert,
        client_key_path=km1_client_key,
        ca_cert_path=km1_ca_cert
    )
    
    km2_client = DirectKMClient(
        base_url="https://localhost:14000",
        sae_id=3,
        client_cert_path=km2_client_cert,
        client_key_path=km2_client_key,
        ca_cert_path=km2_ca_cert
    )
    
    return km1_client, km2_client

# Create global clients for easy access
km1_client, km2_client = create_direct_km_clients()

def get_direct_km_clients():
    """Get the global KM client instances"""
    return km1_client, km2_client
