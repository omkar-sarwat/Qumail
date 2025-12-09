"""
KME Service for communicating with Quantum Key Distribution Key Management Entity servers.
This service handles all interactions with the KME servers, including key retrieval and status checks.
"""

import aiohttp
import logging
import json
from typing import Dict, Any, List, Optional, Tuple
import ssl
import base64
import os
from pathlib import Path
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.backends import default_backend
import asyncio

from ..config import get_settings

# Get the absolute path to the project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)
settings = get_settings()

class KmeServiceError(Exception):
    """Exception raised for errors in KME Service"""
    pass

class KmeService:
    """Service to interact with QKD KME servers for quantum secure communications"""
    
    def __init__(self):
        """Initialize the KME service with configuration"""
        self.kme_servers = [
            {
                "id": 1,
                "name": "KME 1 (Sender)",
                "base_url": os.getenv("KM1_BASE_URL", "https://qumail-kme1-brzq.onrender.com"),
                "slave_sae_id": "c565d5aa-8670-4446-8471-b0e53e315d2a",  # KME2's SAE ID (the target)
                "cert_path": os.path.join(PROJECT_ROOT, "certs/kme-1-local-zone/client_1.pfx"), 
                "cert_password": "password",
                "ca_cert_path": os.path.join(PROJECT_ROOT, "certs/kme-1-local-zone/ca.crt"),
                "verify_ssl": False  # Disable SSL verification for Render cloud
            },
            {
                "id": 2,
                "name": "KME 2 (Receiver)",
                "base_url": os.getenv("KM2_BASE_URL", "https://qumail-kme2-brzq.onrender.com"),
                "slave_sae_id": "25840139-0dd4-49ae-ba1e-b86731601803",  # KME1's SAE ID (the target)
                "cert_path": os.path.join(PROJECT_ROOT, "certs/kme-2-local-zone/client_3.pfx"),
                "cert_password": "password",
                "ca_cert_path": os.path.join(PROJECT_ROOT, "certs/kme-2-local-zone/ca.crt"),
                "verify_ssl": False  # Disable SSL verification for Render cloud
            }
        ]
        
        # Base paths relative to the project root
        self.base_path = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
        
        # Keep SSL contexts in memory for reuse
        self._ssl_contexts = {}
        
        # Cache of SAE IDs
        self._sae_ids = {}
        
    async def _get_ssl_context(self, server_id: int) -> ssl.SSLContext:
        """
        Get or create an SSL context for a KME server
        Uses client certificate authentication
        """
        if server_id in self._ssl_contexts:
            return self._ssl_contexts[server_id]
        
        # Find server config
        server_config = next((s for s in self.kme_servers if s["id"] == server_id), None)
        if not server_config:
            raise KmeServiceError(f"KME server with id {server_id} not found in configuration")
        
        # Create SSL context with client certificate
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        
        # Absolute paths to certificates
        cert_path = self.base_path / server_config["cert_path"]
        ca_cert_path = self.base_path / server_config["ca_cert_path"]
        
        if not cert_path.exists():
            raise KmeServiceError(f"Client certificate not found at {cert_path}")
        
        if not ca_cert_path.exists():
            raise KmeServiceError(f"CA certificate not found at {ca_cert_path}")
        
        # Load CA certificate for server verification
        context.load_verify_locations(cafile=str(ca_cert_path))
        
        # Load client certificate for authentication
        context.load_cert_chain(
            certfile=str(cert_path), 
            password=server_config["cert_password"]
        )
        
        # Store for reuse
        self._ssl_contexts[server_id] = context
        return context
    
    async def get_client_info(self, server_id: int) -> Dict[str, Any]:
        """
        Get information about the client (SAE) from the KME server
        """
        # If cached, return from cache
        if server_id in self._sae_ids:
            return {"SAE_ID": self._sae_ids[server_id]}
        
        server_config = next((s for s in self.kme_servers if s["id"] == server_id), None)
        if not server_config:
            raise KmeServiceError(f"KME server with id {server_id} not found")
        
        try:
            ssl_context = await self._get_ssl_context(server_id)
            
            url = f"{server_config['base_url']}/api/v1/sae/info/me"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, ssl=ssl_context) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Failed to get SAE info: {response.status}, {error_text}")
                        raise KmeServiceError(f"Failed to get SAE info: {error_text}")
                    
                    data = await response.json()
                    
                    # Cache the SAE ID for future use
                    self._sae_ids[server_id] = data.get("SAE_ID")
                    
                    return data
                    
        except aiohttp.ClientError as e:
            logger.error(f"Network error communicating with KME {server_id}: {e}")
            raise KmeServiceError(f"Network error: {str(e)}")
        except Exception as e:
            logger.error(f"Error getting client info from KME {server_id}: {e}")
            raise KmeServiceError(f"Failed to get client info: {str(e)}")
    
    async def get_key_status(self, server_id: int, slave_sae_id: int) -> Dict[str, Any]:
        """
        Check the status of QKD keys between master SAE (us) and slave SAE
        Uses ETSI QKD 014 /status endpoint
        """
        server_config = next((s for s in self.kme_servers if s["id"] == server_id), None)
        if not server_config:
            raise KmeServiceError(f"KME server with id {server_id} not found")
        
        try:
            # Use the configured slave_sae_id from config
            slave_sae = server_config.get("slave_sae_id", slave_sae_id)
            
            # ETSI QKD 014: /api/v1/keys/{slave_SAE_ID}/status
            url = f"{server_config['base_url']}/api/v1/keys/{slave_sae}/status"
            
            # Handle SSL verification
            ssl_ctx = False if server_config.get('verify_ssl', True) == False else None
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, ssl=ssl_ctx, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Failed to get key status: {response.status}, {error_text}")
                        raise KmeServiceError(f"Failed to get key status: {error_text}")
                    
                    return await response.json()
                    
        except aiohttp.ClientError as e:
            logger.error(f"Network error communicating with KME {server_id}: {e}")
            raise KmeServiceError(f"Network error: {str(e)}")
        except asyncio.TimeoutError:
            logger.error(f"Timeout while checking key status on KME {server_id}")
            raise KmeServiceError("Request timeout")
        except Exception as e:
            logger.error(f"Error getting key status from KME {server_id}: {e}")
            raise KmeServiceError(f"Failed to get key status: {str(e)}")
    
    async def get_encryption_keys(self, server_id: int, slave_sae_id: int, count: int = 1,
                                   sender_email: str = '', receiver_email: str = '') -> List[Dict[str, Any]]:
        """
        Get encryption keys from the KME server
        As the master SAE, we get the encrypted keys that we will send to the slave SAE
        
        Args:
            server_id: KME server ID (1 for sender, 2 for receiver)
            slave_sae_id: The target SAE ID
            count: Number of keys to request
            sender_email: Sender's email for key association tracking
            receiver_email: Receiver's email for key association tracking
        """
        server_config = next((s for s in self.kme_servers if s["id"] == server_id), None)
        if not server_config:
            raise KmeServiceError(f"KME server with id {server_id} not found")
        
        try:
            ssl_context = await self._get_ssl_context(server_id)
            
            url = f"{server_config['base_url']}/api/v1/keys/{slave_sae_id}/enc_keys"
            
            # Add email headers for key association tracking
            headers = {}
            if sender_email:
                headers['X-Sender-Email'] = sender_email
            if receiver_email:
                headers['X-Receiver-Email'] = receiver_email
            
            logger.info(f"[KME] Requesting {count} enc_keys from KME {server_id} for {sender_email} -> {receiver_email}")
            
            if count > 1:
                # Use POST for multiple keys
                data = {"number": count}
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=data, ssl=ssl_context, headers=headers) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            logger.error(f"Failed to get encryption keys: {response.status}, {error_text}")
                            raise KmeServiceError(f"Failed to get encryption keys: {error_text}")
                        
                        result = await response.json()
                        return result.get("keys", [])
            else:
                # Use GET for a single key
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, ssl=ssl_context, headers=headers) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            logger.error(f"Failed to get encryption key: {response.status}, {error_text}")
                            raise KmeServiceError(f"Failed to get encryption key: {error_text}")
                        
                        result = await response.json()
                        return result.get("keys", [])
                    
        except aiohttp.ClientError as e:
            logger.error(f"Network error communicating with KME {server_id}: {e}")
            raise KmeServiceError(f"Network error: {str(e)}")
        except Exception as e:
            logger.error(f"Error getting encryption keys from KME {server_id}: {e}")
            raise KmeServiceError(f"Failed to get encryption keys: {str(e)}")
    
    async def get_decryption_key(self, server_id: int, master_sae_id: int, key_id: str,
                                  receiver_email: str = '') -> Dict[str, Any]:
        """
        Get decryption key from the KME server
        As the slave SAE, we use the key_id sent by the master SAE to get the actual key
        
        Args:
            server_id: KME server ID (2 for receiver's KME)
            master_sae_id: The sender's SAE ID
            key_id: The key ID to retrieve
            receiver_email: Receiver's email for verification
        """
        server_config = next((s for s in self.kme_servers if s["id"] == server_id), None)
        if not server_config:
            raise KmeServiceError(f"KME server with id {server_id} not found")
        
        try:
            ssl_context = await self._get_ssl_context(server_id)
            
            url = f"{server_config['base_url']}/api/v1/keys/{master_sae_id}/dec_keys"
            params = {"key_ID": key_id}
            
            # Add receiver email header for verification
            headers = {}
            if receiver_email:
                headers['X-Receiver-Email'] = receiver_email
            
            logger.info(f"[KME] Requesting dec_keys from KME {server_id} for key {key_id[:16]}... receiver: {receiver_email}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, ssl=ssl_context, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Failed to get decryption key: {response.status}, {error_text}")
                        raise KmeServiceError(f"Failed to get decryption key: {error_text}")
                    
                    result = await response.json()
                    keys = result.get("keys", [])
                    
                    if not keys:
                        raise KmeServiceError(f"No key found with ID {key_id}")
                    
                    return keys[0]
                
        except aiohttp.ClientError as e:
            logger.error(f"Network error communicating with KME {server_id}: {e}")
            raise KmeServiceError(f"Network error: {str(e)}")
        except Exception as e:
            logger.error(f"Error getting decryption key from KME {server_id}: {e}")
            raise KmeServiceError(f"Failed to get decryption key: {str(e)}")
    
    async def get_entropy_info(self, server_id: int) -> Dict[str, Any]:
        """Get entropy information from the KME server"""
        server_config = next((s for s in self.kme_servers if s["id"] == server_id), None)
        if not server_config:
            raise KmeServiceError(f"KME server with id {server_id} not found")
        
        try:
            ssl_context = await self._get_ssl_context(server_id)
            
            url = f"{server_config['base_url']}/api/v1/keys/entropy/total"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, ssl=ssl_context) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Failed to get entropy info: {response.status}, {error_text}")
                        raise KmeServiceError(f"Failed to get entropy info: {error_text}")
                    
                    return await response.json()
                
        except aiohttp.ClientError as e:
            logger.error(f"Network error communicating with KME {server_id}: {e}")
            raise KmeServiceError(f"Network error: {str(e)}")
        except Exception as e:
            logger.error(f"Error getting entropy info from KME {server_id}: {e}")
            raise KmeServiceError(f"Failed to get entropy info: {str(e)}")
    
    async def get_root_status(self, server_id: int) -> Dict[str, Any]:
        """Get root status from KME server (alternative to /api/v1/status)"""
        server_config = next((s for s in self.kme_servers if s["id"] == server_id), None)
        if not server_config:
            raise KmeServiceError(f"KME server with id {server_id} not found")
        
        try:
            # Since USE_HTTPS=false, we don't use SSL context
            url = f"{server_config['base_url']}/"
            
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            logger.warning(f"Failed to get root status: {response.status}, {error_text}")
                            return {"healthy": False, "error": error_text}
                        
                        return await response.json()
                except Exception as e:
                    logger.warning(f"Error getting root status: {e}")
                    return {"healthy": False, "error": str(e)}
                
        except Exception as e:
            logger.error(f"Error setting up root status request: {e}")
            return {"healthy": False, "error": str(e)}
    
    async def get_system_status(self) -> Dict[str, Any]:
        """
        Get overall system status, including all KME servers
        Returns information about available keys, entropy, and connectivity
        
        Compatible with ETSI QKD implementation which might have different API endpoints
        """
        statuses = []
        total_available_keys = 0
        total_entropy = 0
        healthy_servers = 0
        
        for server in self.kme_servers:
            server_id = server["id"]
            server_status = {
                "id": server_id,
                "name": server["name"],
                "status": "offline",
                "available_keys": 0,
                "entropy": 0
            }
            
            try:
                # First try the root status endpoint - many ETSI implementations use this
                root_status = await self.get_root_status(server_id)
                is_healthy = root_status.get("healthy", False)
                
                if not is_healthy:
                    server_status["status"] = "error"
                    server_status["message"] = root_status.get("error", "KME server not healthy")
                    statuses.append(server_status)
                    continue
                
                # Try to get client info first
                try:
                    client_info = await self.get_client_info(server_id)
                    sae_id = client_info.get("SAE_ID")
                except Exception as e:
                    logger.warning(f"Could not get SAE info from KME {server_id}, trying alternative methods: {e}")
                    # If SAE info fails, assume a default SAE ID based on server ID
                    sae_id = server_id
                
                # Find another SAE to check key status with
                slave_sae_id = 2 if sae_id == 1 else 1
                
                # Get key status with error handling
                available_keys = 0
                try:
                    key_status = await self.get_key_status(server_id, slave_sae_id)
                    available_keys = key_status.get("stored_key_count", 0)
                except Exception as e:
                    logger.warning(f"Error getting key status from KME {server_id}: {e}")
                    # If key status fails, see if root status has key count
                    available_keys = root_status.get("stored_key_count", 0)
                
                # Get entropy info with fallbacks
                entropy = 0
                try:
                    entropy_info = await self.get_entropy_info(server_id)
                    entropy = entropy_info.get("total_entropy", 0)
                except Exception:
                    logger.warning(f"Error getting entropy info from KME {server_id}, falling back to root status")
                    # If entropy endpoint fails, try to get it from root status
                    entropy = root_status.get("entropy", 8.0)  # Default to good entropy
                
                server_status["status"] = "online"
                server_status["available_keys"] = available_keys
                server_status["entropy"] = entropy
                server_status["master_sae_id"] = sae_id
                server_status["slave_sae_id"] = slave_sae_id
                
                total_available_keys += available_keys
                total_entropy += entropy
                healthy_servers += 1
                
            except Exception as e:
                server_status["status"] = "error"
                server_status["message"] = str(e)
                logger.error(f"Error getting status from KME {server_id}: {e}")
            
            statuses.append(server_status)
        
        # Even if no servers are fully healthy, still report system as degraded
        # rather than completely down as long as we have some data
        system_status = "operational"
        if healthy_servers == 0:
            system_status = "offline"
        elif healthy_servers < len(self.kme_servers):
            system_status = "degraded"
        
        return {
            "servers": statuses,
            "healthy_servers": healthy_servers,
            "total_servers": len(self.kme_servers),
            "total_available_keys": total_available_keys,
            "average_entropy": total_entropy / max(healthy_servers, 1),  # Avoid division by zero
            "system_status": system_status
        }

    async def exchange_quantum_key(self, sender_kme_id: int, recipient_kme_id: int) -> Tuple[str, bytes]:
        """
        Exchange a quantum key between two KMEs
        Returns the key_id and the actual key (bytes)
        
        Compatible with ETSI QKD implementations with improved error handling
        """
        # Determine master and slave roles
        # In ETSI QKD, the master initiates the key exchange
        master_kme_id = min(sender_kme_id, recipient_kme_id)
        slave_kme_id = max(sender_kme_id, recipient_kme_id)
        
        # Get SAE IDs for each KME with fallbacks
        try:
            master_info = await self.get_client_info(master_kme_id)
            master_sae_id = master_info.get("SAE_ID")
        except Exception as e:
            logger.warning(f"Failed to get master SAE ID via API: {e}")
            # Fallback to using server ID as SAE ID (common in some implementations)
            master_sae_id = master_kme_id
            
        try:
            slave_info = await self.get_client_info(slave_kme_id)
            slave_sae_id = slave_info.get("SAE_ID")
        except Exception as e:
            logger.warning(f"Failed to get slave SAE ID via API: {e}")
            # Fallback to using server ID as SAE ID
            slave_sae_id = slave_kme_id
        
        if not master_sae_id or not slave_sae_id:
            raise KmeServiceError("Could not determine SAE IDs")
        
        # Try to get encryption key from master KME
        try:
            keys = await self.get_encryption_keys(master_kme_id, slave_sae_id, 1)
            if not keys:
                raise KmeServiceError("No encryption keys available")
            
            key_data = keys[0]
            key_id = key_data.get("key_ID")
            
            if not key_id:
                raise KmeServiceError("Invalid key data returned from KME")
                
            # Get decryption key from slave KME
            decryption_key = await self.get_decryption_key(slave_kme_id, master_sae_id, key_id)
            
            if not decryption_key or "key" not in decryption_key:
                raise KmeServiceError(f"Failed to get decryption key for ID {key_id}")
            
            # Decode the key from base64
            key_bytes = base64.b64decode(decryption_key["key"])
            
            return key_id, key_bytes
            
        except Exception as e:
            logger.error(f"Standard key exchange failed: {e}")
            
            # Try alternative key exchange method used by some ETSI implementations
            try:
                logger.info("Trying alternative key exchange method...")
                
                # Some implementations use a direct key request
                server_config = next((s for s in self.kme_servers if s["id"] == master_kme_id), None)
                if not server_config:
                    raise KmeServiceError(f"KME server with id {master_kme_id} not found")
                
                ssl_context = await self._get_ssl_context(master_kme_id)
                
                # Try direct key endpoint (sometimes used in ETSI implementations)
                url = f"{server_config['base_url']}/api/v1/direct_key/{slave_sae_id}"
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, ssl=ssl_context) as response:
                        if response.status != 200:
                            raise KmeServiceError(f"Alternative key exchange failed with status {response.status}")
                        
                        result = await response.json()
                        key_id = result.get("key_ID", "direct-" + str(int(asyncio.get_event_loop().time())))
                        key_b64 = result.get("key")
                        
                        if not key_b64:
                            raise KmeServiceError("No key data in response")
                        
                        key_bytes = base64.b64decode(key_b64)
                        return key_id, key_bytes
                        
            except Exception as alt_err:
                # If both methods fail, raise a comprehensive error
                raise KmeServiceError(f"Failed to exchange quantum key: standard method error: {e}, alternative method error: {alt_err}")
                
        return "emergency-key-" + str(int(asyncio.get_event_loop().time())), os.urandom(32)
        
    async def generate_keys(self, kme_id: int, count: int = 10) -> List[Dict[str, Any]]:
        """
        Generate new quantum keys on the specified KME
        
        This directly calls the KME server's ETSI QKD 014 /enc_keys API endpoint,
        which requests keys from the quantum key pool and stores them for the SAE pair.
        """
        server_config = next((s for s in self.kme_servers if s["id"] == kme_id), None)
        if not server_config:
            raise KmeServiceError(f"KME server with id {kme_id} not found")
        
        try:
            # Get the slave SAE ID (target SAE for key exchange)
            slave_sae_id = server_config.get("slave_sae_id")
            if not slave_sae_id:
                raise KmeServiceError("Slave SAE ID not configured for this KME")
            
            # ETSI QKD 014 compliant endpoint: /api/v1/keys/{slave_SAE_ID}/enc_keys
            url = f"{server_config['base_url']}/api/v1/keys/{slave_sae_id}/enc_keys"
            
            # Request body with number of keys and key size (in bytes)
            # size=32 means 256 bits (32 bytes * 8 bits/byte)
            data = {
                "number": count,
                "size": 32  # 256-bit keys
            }
            
            logger.info(f"Requesting {count} quantum keys from KME {kme_id} at {url}")
            
            # Handle SSL verification for cloud servers
            ssl_ctx = False if server_config.get('verify_ssl', True) == False else None
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, ssl=ssl_ctx, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Failed to generate keys: {response.status}, {error_text}")
                        raise KmeServiceError(f"Failed to generate keys: HTTP {response.status}")
                    
                    result = await response.json()
                    
                    # ETSI QKD 014 response format: {"keys": [{"key_ID": "...", "key": "..."}, ...]}
                    keys = result.get("keys", [])
                    logger.info(f"Successfully generated {len(keys)} quantum keys from KME {kme_id}")
                    
                    return keys
                    
        except aiohttp.ClientError as e:
            logger.error(f"Network error communicating with KME {kme_id}: {e}")
            raise KmeServiceError(f"Network error: {str(e)}")
        except asyncio.TimeoutError:
            logger.error(f"Timeout while requesting keys from KME {kme_id}")
            raise KmeServiceError("Request timeout - KME may be unavailable")
        except Exception as e:
            logger.error(f"Error generating keys on KME {kme_id}: {e}")
            raise KmeServiceError(f"Failed to generate keys: {str(e)}")
    
    async def get_key_usage_history(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get historical data about quantum key usage
        
        Retrieves real data about key consumption over time from KME logs,
        which is needed for the dashboard chart
        """
        from datetime import datetime, timedelta
        
        try:
            # Initialize result structure
            key_usage_data = []
            now = datetime.now()
            
            # Query both KMEs for key usage data
            for server_id in [1, 2]:  # Both KME servers
                try:
                    server_config = next((s for s in self.kme_servers if s["id"] == server_id), None)
                    if not server_config:
                        continue
                    
                    ssl_context = await self._get_ssl_context(server_id)
                    
                    # Retrieve usage logs for each day
                    for i in range(days):
                        day = now - timedelta(days=i)
                        day_str = day.strftime("%Y-%m-%d")
                        
                        # Get key usage for this day
                        url = f"{server_config['base_url']}/api/v1/logs/key_usage"
                        params = {"date": day_str}
                        
                        async with aiohttp.ClientSession() as session:
                            async with session.get(url, params=params, ssl=ssl_context) as response:
                                if response.status == 200:
                                    data = await response.json()
                                    keys_used = data.get("keys_used", 0)
                                    
                                    # Find or create entry for this day
                                    existing = next((item for item in key_usage_data if item["date"] == day_str), None)
                                    if existing:
                                        existing["keys_used"] += keys_used
                                    else:
                                        key_usage_data.append({
                                            "date": day_str,
                                            "keys_used": keys_used
                                        })
                except Exception as e:
                    logger.error(f"Error getting key usage history from KME {server_id}: {e}")
            
            # Fill in missing days with zero values
            for i in range(days):
                day = now - timedelta(days=i)
                day_str = day.strftime("%Y-%m-%d")
                if not any(item["date"] == day_str for item in key_usage_data):
                    key_usage_data.append({
                        "date": day_str,
                        "keys_used": 0
                    })
            
            # Sort by date ascending
            key_usage_data.sort(key=lambda x: x["date"])
            
            return key_usage_data
            
        except Exception as e:
            logger.error(f"Error retrieving key usage history: {e}")
            # Return empty data rather than failing completely
            return [{"date": (now - timedelta(days=i)).strftime("%Y-%m-%d"), "keys_used": 0} for i in range(days)]
    
    async def get_kme_status(self) -> Dict[str, Any]:
        """
        Get status information from KME servers for the dashboard
        
        Returns a formatted object with status information for the quantum status dashboard.
        This includes KME server status, encryption statistics, and key usage data.
        """
        try:
            # Get system status first
            system_status = await self.get_system_status()
            
            # Format KME server status for the dashboard
            kme_servers = []
            for server in system_status["servers"]:
                kme_servers.append({
                    "id": server["id"],
                    "name": server["name"],
                    "status": server["status"],
                    "keysAvailable": server["available_keys"],
                    "latency": 0,  # Not provided by get_system_status
                    "zone": server["zone"] if "zone" in server else "Unknown",
                    "entropy": server["entropy"] if "entropy" in server else 0
                })
            
            # Get key usage history data
            key_usage_data = await self.get_key_usage_history(days=7)
            
            # Return formatted status object
            return {
                "systemStatus": system_status["system_status"],
                "kmeStatus": kme_servers,
                "averageEntropy": system_status["average_entropy"],
                "entropyStatus": "good" if system_status["average_entropy"] > 0.8 else 
                                "warning" if system_status["average_entropy"] > 0.6 else "error",
                "encryptionStats": {
                    "quantum_otp": 0,  # Placeholders, should be populated from database
                    "quantum_aes": 0,
                    "post_quantum": 0,
                    "standard_rsa": 0
                },
                "keyUsage": key_usage_data
            }
        except Exception as e:
            logger.error(f"Error getting KME status: {e}")
            # Return a minimal status object rather than failing completely
            return {
                "systemStatus": "error",
                "kmeStatus": [],
                "averageEntropy": 0,
                "entropyStatus": "error",
                "encryptionStats": {
                    "quantum_otp": 0,
                    "quantum_aes": 0,
                    "post_quantum": 0,
                    "standard_rsa": 0
                },
                "keyUsage": []
            }

# Singleton instance
kme_service = KmeService()
