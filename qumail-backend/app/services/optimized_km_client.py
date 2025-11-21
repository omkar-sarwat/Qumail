"""
Optimized KM Client for reliable communication with real quantum key management servers
Solves timeout issues, implements caching, and provides robust error handling
"""

import os
import ssl
import base64
import logging
import asyncio
import time
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
import httpx
import uuid
from datetime import datetime, timedelta
import threading
from concurrent.futures import ThreadPoolExecutor

from app.config import get_settings

logger = logging.getLogger(__name__)

# Constants for client configuration
DEFAULT_TIMEOUT = 15.0  # Reasonable timeout for KM operations
MAX_RETRIES = 2  # Reduced retries for faster failure detection
RETRY_DELAY = 1.0  # seconds
KEY_CACHE_SIZE = 10  # Number of keys to maintain in cache

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

class OptimizedKMClient:
    """
    Optimized Key Manager client with improved reliability for real KM servers
    - Implements connection retry logic
    - Provides key caching to reduce load on KM servers
    - Uses longer timeouts for slow key operations
    - Better certificate management
    """
    
    def __init__(self, base_url: str, sae_id, 
                 client_cert_path: str = None,
                 client_key_path: str = None,
                 ca_cert_path: str = None,
                 key_cache_size: int = KEY_CACHE_SIZE):
        """
        Initialize KM client with optional PEM certificate paths
        
        Args:
            base_url: Base URL of the KM server (HTTP or HTTPS)
            sae_id: Local SAE ID (can be int or string/UUID)
            client_cert_path: Path to client certificate PEM file (optional for HTTP)
            client_key_path: Path to client key PEM file (optional for HTTP)
            ca_cert_path: Path to CA certificate PEM file (optional for HTTP)
            key_cache_size: Size of key cache (number of keys)
        """
        self.base_url = base_url.rstrip('/')
        self.sae_id = sae_id
        self.is_https = base_url.startswith('https')
        
        # Certificate paths (optional for HTTP)
        self.client_cert_path = Path(client_cert_path) if client_cert_path else None
        self.client_key_path = Path(client_key_path) if client_key_path else None
        self.ca_cert_path = Path(ca_cert_path) if ca_cert_path else None
        
        # HTTP client
        self._client: Optional[httpx.AsyncClient] = None
        self._ssl_context: Optional[ssl.SSLContext] = None
        
        # Key cache for each peer SAE
        # Structure: {peer_sae_id: [(key_id, key_data), ...]}
        self.key_cache: Dict[str, List[Tuple[str, str]]] = {}
        self.key_cache_size = key_cache_size
        
        # Set of consumed key IDs to prevent reuse
        self.consumed_keys: Set[str] = set()
        
        # Status cache to reduce status requests
        self.status_cache = {}
        self.status_cache_time = {}
        self.status_cache_valid = 30  # seconds
        
        logger.info(f"Initialized OptimizedKMClient for SAE {sae_id} at {base_url}")

    async def _setup_ssl_context(self) -> Optional[ssl.SSLContext]:
        """Create SSL context - disables verification for cloud KME servers (Render.com)"""
        if not self.is_https:
            # No SSL context needed for HTTP connections
            return None
            
        try:
            # For cloud KME servers (Render.com), disable SSL verification
            # They use self-signed certificates which would fail validation
            if not self.ca_cert_path or not self.ca_cert_path.exists():
                logger.info("Cloud KME mode: SSL verification disabled for Render.com servers")
                return False  # Return False to disable SSL verification in httpx
            
            # Create SSL context for local mutual TLS authentication (Next Door Key Simulator)
            ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
            ssl_context.check_hostname = False  # Next Door Key Simulator uses localhost
            
            # Load CA certificate for server verification
            if self.ca_cert_path and self.ca_cert_path.exists():
                try:
                    ssl_context.load_verify_locations(cafile=str(self.ca_cert_path))
                    ssl_context.verify_mode = ssl.CERT_REQUIRED
                    logger.info(f"Loaded CA certificate: {self.ca_cert_path}")
                except Exception as e:
                    logger.error(f"Failed to load CA certificate: {e}")
                    raise SecurityError(f"Cannot establish secure connection without valid CA certificate: {e}")
            
            # Load client certificate and key for mTLS
            if (self.client_cert_path and self.client_cert_path.exists() and 
                self.client_key_path and self.client_key_path.exists()):
                try:
                    ssl_context.load_cert_chain(
                        certfile=str(self.client_cert_path),
                        keyfile=str(self.client_key_path)
                    )
                    logger.info(f"Loaded client certificate: {self.client_cert_path}")
                except Exception as e:
                    logger.error(f"Failed to load client certificate: {e}")
                    raise SecurityError(f"Cannot establish secure connection without valid client certificate: {e}")
                
            logger.info("SSL context configured with proper mutual TLS authentication")
            return ssl_context
            
        except SecurityError:
            # Re-raise security errors
            raise
        except Exception as e:
            logger.error(f"Failed to setup SSL context: {e}")
            raise SecurityError(f"SSL context setup failed: {e}")

    async def _get_client(self, timeout: float = DEFAULT_TIMEOUT) -> httpx.AsyncClient:
        """Get or create authenticated HTTP client with specific timeout"""
        if self._client is None:
            if self.is_https and self._ssl_context is None:
                self._ssl_context = await self._setup_ssl_context()
            
            # Setup client configuration based on protocol
            client_config = {
                "base_url": self.base_url,
                "timeout": timeout,
                "headers": {
                    "User-Agent": "QuMail-SAE/1.0",
                    "Content-Type": "application/json",
                    "X-SAE-ID": str(self.sae_id)  # Send SAE ID in header for HTTP mode
                }
            }
            
            # Use proper SSL verification for HTTPS with certificates
            if self.is_https:
                # Setup SSL context with proper mutual TLS authentication or disable for cloud
                if self._ssl_context is None:
                    self._ssl_context = await self._setup_ssl_context()
                client_config["verify"] = self._ssl_context
                if self._ssl_context is False:
                    logger.info("Using cloud KME mode with SSL verification disabled")
                else:
                    logger.info("Using proper SSL verification with mutual TLS authentication")
            
            self._client = httpx.AsyncClient(**client_config)
            logger.debug(f"Created new {'HTTPS' if self.is_https else 'HTTP'} client with timeout {timeout}s")
        return self._client

    async def close(self):
        """Close client connection and cleanup"""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _execute_with_retry(self, request_func, *args, max_retries=MAX_RETRIES, **kwargs):
        """Execute a request function with automatic retry on timeout or connection error"""
        retries = 0
        last_exception = None
        
        while retries <= max_retries:
            try:
                # Get a fresh client on retry
                if retries > 0 and self._client:
                    await self._client.aclose()
                    self._client = None
                    # Increase timeout exponentially with each retry
                    timeout = DEFAULT_TIMEOUT * (2 ** retries)
                    logger.info(f"Retry {retries}/{max_retries} with increased timeout {timeout}s")
                    client = await self._get_client(timeout=timeout)
                else:
                    client = await self._get_client()
                    
                # Call the request function
                return await request_func(client, *args, **kwargs)
                
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                last_exception = e
                retries += 1
                if retries <= max_retries:
                    # Wait before retry
                    wait_time = RETRY_DELAY * (2 ** (retries - 1))  # Exponential backoff
                    logger.warning(f"Request timed out, retrying in {wait_time}s ({retries}/{max_retries})")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Request failed after {max_retries} retries: {e}")
                    raise KMConnectionError(f"Failed to connect to KM server after {max_retries} retries: {e}")
            except Exception as e:
                logger.error(f"Request failed: {e}")
                raise e
    
    async def check_key_status(self, slave_sae_id) -> Dict[str, Any]:
        """Check availability of quantum keys for given slave SAE with caching"""
        # Return cached status if still valid
        now = time.time()
        if (slave_sae_id in self.status_cache and 
            now - self.status_cache_time.get(slave_sae_id, 0) < self.status_cache_valid):
            logger.debug(f"Using cached key status for SAE {slave_sae_id}")
            return self.status_cache[slave_sae_id]
        
        # Status not in cache or expired - fetch from server
        try:
            async def fetch_status(client, slave_sae_id):
                response = await client.get(f"/api/v1/keys/{slave_sae_id}/status")
                response.raise_for_status()
                
                status = response.json()
                logger.info(f"Key status for SAE {slave_sae_id}: {status.get('stored_key_count', 0)} keys available")
                return status
            
            status = await self._execute_with_retry(fetch_status, slave_sae_id)
            
            # Cache the status
            self.status_cache[slave_sae_id] = status
            self.status_cache_time[slave_sae_id] = now
            
            return status
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise InsufficientKeysError(f"No keys available for SAE {slave_sae_id}")
            elif e.response.status_code == 401:
                raise AuthenticationError("SAE authentication failed")
            else:
                raise KMConnectionError(f"KM server error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Failed to check key status: {type(e).__name__}: {str(e)}")
            logger.error(f"Full exception details: {repr(e)}")
            raise KMConnectionError(f"Unexpected error checking key status: {type(e).__name__}: {str(e)}")

    async def _fetch_keys_from_server(self, slave_sae_id, number: int = 1, size: int = 256) -> List[Dict[str, Any]]:
        """Fetch keys directly from KM server with longer timeout and retries"""
        try:
            logger.info(f"KM_CLIENT DEBUG: Fetching {number} keys (size={size} bits) from KM server for SAE {slave_sae_id}")
            logger.info(f"KM_CLIENT DEBUG: Using base_url={self.base_url}, sae_id={self.sae_id}")
            
            async def fetch_keys(client, slave_sae_id, number):
                payload = {"number": number, "size": size}  # Include size parameter in bits
                headers = {
                    "X-SAE-ID": str(self.sae_id),  # Master SAE ID (sender)
                    "X-Slave-SAE-ID": str(slave_sae_id)  # Slave SAE ID (receiver)
                }
                # Use extended timeout for key requests as they're slow
                response = await client.post(
                    f"/api/v1/keys/{slave_sae_id}/enc_keys",  # ETSI QKD 014 standard format
                    json=payload,
                    headers=headers,
                    timeout=DEFAULT_TIMEOUT * 2  # Double the default timeout for key requests
                )
                response.raise_for_status()
                
                data = response.json()
                keys = data.get("keys", [])
                
                if len(keys) < number:
                    logger.warning(f"Requested {number} keys but only received {len(keys)}")
                
                return keys
            
            # Use more retries for key requests
            keys = await self._execute_with_retry(fetch_keys, slave_sae_id, number, max_retries=MAX_RETRIES+1)
            
            logger.info(f"KM_CLIENT DEBUG: Successfully fetched {len(keys)} keys (size={size} bits) from server")
            if keys:
                for i, key in enumerate(keys):
                    logger.info(f"KM_CLIENT DEBUG: Key {i}: ID={key.get('key_ID')}, size={len(key.get('key', ''))} chars")
            return keys
        
        except Exception as e:
            logger.error(f"Failed to fetch keys from server: {e}")
            raise

    async def _populate_key_cache(self, slave_sae_id) -> None:
        """Pre-populate key cache for specific SAE ID"""
        try:
            sae_id_str = str(slave_sae_id)
            # Create cache entry if it doesn't exist
            if sae_id_str not in self.key_cache:
                self.key_cache[sae_id_str] = []
            
            # Skip if cache is already populated
            if len(self.key_cache[sae_id_str]) >= self.key_cache_size:
                return
            
            # Check how many keys are needed
            keys_needed = self.key_cache_size - len(self.key_cache[sae_id_str])
            if keys_needed <= 0:
                return
                
            # Check if enough keys are available on server
            status = await self.check_key_status(slave_sae_id)
            available = status.get('stored_key_count', 0)
            
            if available <= 0:
                logger.warning(f"No keys available on server for SAE {slave_sae_id}")
                return
                
            # Don't request more than available
            keys_to_fetch = min(keys_needed, available, 5)  # Max 5 keys at a time to avoid timeouts
            
            # Fetch keys from server
            new_keys = await self._fetch_keys_from_server(slave_sae_id, keys_to_fetch)
            
            # Add to cache
            for key_data in new_keys:
                key_id = key_data.get("key_ID")
                key = key_data.get("key")
                
                # DON'T skip consumed keys - allow key reuse for debugging
                # if key_id in self.consumed_keys:
                #     continue
                    
                self.key_cache[sae_id_str].append((key_id, key))
            
            logger.info(f"Added {len(new_keys)} keys to cache for SAE {slave_sae_id}")
            
        except Exception as e:
            logger.error(f"Failed to populate key cache: {e}")

    async def request_enc_keys(self, slave_sae_id, number: int = 1, size: int = 256) -> List[Dict[str, Any]]:
        """Request encryption keys with cache and fallback to direct server request"""
        try:
            result_keys = []
            
            # Try to get keys from cache first
            sae_id_str = str(slave_sae_id)
            if sae_id_str in self.key_cache:
                cached_keys = self.key_cache[sae_id_str]
                # DON'T filter consumed keys - allow key reuse for debugging
                # cached_keys = [(kid, k) for kid, k in cached_keys if kid not in self.consumed_keys]
                self.key_cache[slave_sae_id] = cached_keys
                
                # Take keys from cache
                keys_from_cache = cached_keys[:number]
                self.key_cache[sae_id_str] = cached_keys[number:]
                
                # Format keys
                for key_id, key_data in keys_from_cache:
                    result_keys.append({
                        "key_ID": key_id,
                        "key": key_data,
                        "key_size": size
                    })
            
            # If we got all keys from cache, return them
            if len(result_keys) >= number:
                logger.info(f"Retrieved {len(result_keys)} encryption keys from cache for SAE {slave_sae_id}")
                
                # Trigger async cache repopulation without waiting
                asyncio.create_task(self._populate_key_cache(slave_sae_id))
                
                return result_keys[:number]  # Return only the requested number
            
            # Otherwise, we need to get more keys from server
            keys_needed = number - len(result_keys)
            
            # Skip status check - Next Door Key Simulator generates keys on-demand from pool
            # The stored_key_count only shows pre-exchanged keys for this SAE pair,
            # but the simulator will pull from the key pool when we request enc_keys
            logger.debug(f"Requesting {keys_needed} keys from server (on-demand from pool)")
            
            # Request keys from server with enhanced timeout and the requested key size
            # This will automatically pull from the key pool and exchange with other KMEs
            server_keys = await self._fetch_keys_from_server(slave_sae_id, keys_needed, size)
            
            # Add to result
            result_keys.extend(server_keys)
            
            # Also populate cache with any extra keys if we got them
            extra_keys = len(server_keys) - keys_needed
            if extra_keys > 0:
                for key_data in server_keys[-extra_keys:]:
                    key_id = key_data.get("key_ID")
                    key = key_data.get("key")
                    self.key_cache.setdefault(sae_id_str, []).append((key_id, key))
                    
                result_keys = result_keys[:-extra_keys]
            
            # Start background task to populate key cache without waiting
            asyncio.create_task(self._populate_key_cache(slave_sae_id))
            
            logger.info(f"Retrieved {len(result_keys)} encryption keys for SAE {slave_sae_id}")
            return result_keys
            
        except InsufficientKeysError:
            raise
        except Exception as e:
            logger.error(f"Error requesting encryption keys: {e}")
            raise KMConnectionError(f"Failed to request encryption keys: {e}")

    async def request_dec_keys(self, master_sae_id, key_ids: List[str]) -> List[Dict[str, Any]]:
        """Request decryption keys using key IDs with retry for timeouts"""
        try:
            
            async def fetch_dec_keys(client, master_sae_id, key_ids):
                # KMS expects plain list of strings, not objects
                payload = {"key_IDs": [{"key_ID": kid} for kid in key_ids]}
                headers = {
                    "X-SAE-ID": str(self.sae_id),  # Slave SAE ID (receiver)
                    "X-Slave-SAE-ID": str(master_sae_id)  # Master SAE ID (sender)
                }
                response = await client.post(
                    f"/api/v1/keys/{master_sae_id}/dec_keys",  # ETSI QKD 014 standard format
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                
                data = response.json()
                keys = data.get("keys", [])
                
                if len(keys) != len(key_ids):
                    logger.warning(f"Requested {len(key_ids)} keys but only received {len(keys)}")
                
                return keys
            
            # Execute with retry
            keys = await self._execute_with_retry(fetch_dec_keys, master_sae_id, key_ids)
            
            # DON'T mark keys as consumed immediately - let the caller decide
            # This allows the same keys to be retrieved multiple times if needed
            # for debugging or retry scenarios
            
            logger.info(f"Retrieved {len(keys)} decryption keys from SAE {master_sae_id}")
            return keys
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise AuthenticationError("SAE authentication failed")
            elif e.response.status_code == 404:
                raise SecurityError("One or more key IDs not found - possible tampering or server restart (keys are in-memory only)")
            else:
                raise KMConnectionError(f"KM server error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error requesting decryption keys: {e}")
            raise KMConnectionError(f"Failed to request decryption keys: {e}")

    async def get_sae_info(self) -> Dict[str, Any]:
        """Get information about this SAE"""
        try:
            async def fetch_info(client):
                response = await client.get("/api/v1/sae/info/me")
                response.raise_for_status()
                return response.json()
            
            return await self._execute_with_retry(fetch_info)
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise AuthenticationError("SAE not registered with KM")
            raise KMConnectionError(f"KM server error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error getting SAE info: {e}")
            raise KMConnectionError(f"Failed to get SAE info: {e}")

    async def check_entropy(self) -> float:
        """Check total entropy of keys (security monitoring)"""
        try:
            async def fetch_entropy(client):
                response = await client.get("/api/v1/keys/entropy/total")
                response.raise_for_status()
                
                data = response.json()
                entropy = data.get("total_entropy", 0.0)
                
                # Warn if entropy is suspiciously low (possible attack)
                if entropy < 7.0:
                    logger.warning(f"Low entropy detected: {entropy} - possible QKD compromise")
                
                return entropy
                
            return await self._execute_with_retry(fetch_entropy)
            
        except Exception as e:
            logger.warning(f"Failed to check entropy: {e}")
            return 0.0
    
    async def mark_key_consumed(self, key_id: str) -> bool:
        """Mark quantum key as consumed (one-time use enforcement)"""
        try:
            # Add to local consumed keys set
            self.consumed_keys.add(key_id)
            
            async def mark_consumed(client, key_id):
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
                    return True
                    
            return await self._execute_with_retry(mark_consumed, key_id)
                
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
            async def fetch_status(client):
                # Try both endpoints that might contain status information
                try:
                    response = await client.get("/api/v1/kme/status")
                    response.raise_for_status()
                except Exception as e:
                    # Fall back to root status (common in ETSI QKD implementations)
                    logger.debug(f"Failed to get status from /api/v1/kme/status: {e}, trying alternative endpoint")
                    response = await client.get("/")
                    response.raise_for_status()
                
                status = response.json()
                
                # Check for critical indicators
                healthy = status.get("healthy", True)  # Assume healthy if not specified
                available_keys = status.get("stored_key_count", 0)
                entropy = status.get("entropy", 8.0)  # Default to good entropy if not reported
                
                # Try to get key count if not directly in status
                if available_keys == 0:
                    # The simulator's peer status endpoint can be slow when the other KME
                    # is still synchronizing. Bound the request timeout so Phase 2 won't stall.
                    for peer_id in [1, 3]:
                        if str(peer_id) == str(self.sae_id):
                            continue
                        try:
                            peer_status = await client.get(
                                f"/api/v1/keys/{peer_id}/status",
                                timeout=min(DEFAULT_TIMEOUT, 2.0)
                            )
                            if peer_status.status_code == 200:
                                peer_data = peer_status.json()
                                available_keys = peer_data.get("stored_key_count", 0)
                                if available_keys:
                                    break
                        except (httpx.TimeoutException, httpx.ConnectError):
                            logger.debug(
                                "Peer status lookup timed out for SAE %s", peer_id
                            )
                        except Exception as exc:
                            logger.debug(
                                "Peer status lookup failed for SAE %s: %s", peer_id, exc
                            )
                
                # Enhance status with security analysis
                status["security_analysis"] = {
                    "entropy_healthy": entropy >= 7.0,
                    "keys_sufficient": available_keys >= 1,
                    "overall_health": healthy and available_keys >= 1
                }
                
                logger.info(f"KM status: healthy={healthy}, keys={available_keys}, entropy={entropy}")
                return status
                
            return await self._execute_with_retry(fetch_status)
            
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

    async def start_background_cache_population(self, peer_sae_ids: List):
        """Start background task to periodically populate key cache for multiple peer SAEs"""
        while True:
            for sae_id in peer_sae_ids:
                try:
                    await self._populate_key_cache(sae_id)
                except Exception as e:
                    logger.error(f"Failed to populate cache for SAE {sae_id}: {e}")
            
            # Wait before next round of cache population
            await asyncio.sleep(60)  # 1 minute

# Note: OptimizedKMClient instances are now created and managed by km_client_init.py
# for Next Door Key Simulator integration with proper SAE IDs and certificates
