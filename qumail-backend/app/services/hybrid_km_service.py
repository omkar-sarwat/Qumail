"""
Hybrid KM Service that combines OptimizedKMClient and RealQKDClient
This service handles the fallback mechanism for when KME servers have inter-communication issues
"""

import os
import sys
import base64
import logging
import uuid
import asyncio
import binascii
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional, Set

from .optimized_km_client import OptimizedKMClient, KMConnectionError, InsufficientKeysError
from .real_qkd_client import RealQKDClient, RealQuantumKeyError

logger = logging.getLogger(__name__)

class HybridKMError(Exception):
    """Base class for hybrid KM service errors"""
    pass

class HybridKMService:
    """
    Hybrid service that combines OptimizedKMClient and RealQKDClient
    
    This service provides a reliable mechanism for retrieving quantum keys:
    1. First attempts to use the OptimizedKMClient for KME server communication
    2. Falls back to RealQKDClient for direct raw key file access if the KME server fails
    3. Provides a unified API for the rest of the application
    """
    
    def __init__(self):
        """Initialize the hybrid KM service with clients"""
        # Keep track of consumed keys to prevent reuse
        self.consumed_keys: Set[str] = set()
        
        # Try to initialize the clients
        try:
            # Initialize optimized KM clients
            from .km_client_init import get_optimized_km_clients
            self.km1, self.km2 = get_optimized_km_clients()
            
            # Initialize real QKD clients
            from .real_qkd_client import create_real_qkd_clients
            self.real_km1, self.real_km2 = create_real_qkd_clients()
            
            logger.info("Hybrid KM Service initialized with both optimized and real clients")
            
        except Exception as e:
            logger.error(f"Failed to initialize Hybrid KM Service: {e}")
            raise HybridKMError(f"Failed to initialize Hybrid KM Service: {e}")
    
    async def check_key_status(self, kme_id: int, slave_sae_id: int) -> Dict[str, Any]:
        """Check key status using optimized KM client (this endpoint usually works)"""
        try:
            km = self.km1 if kme_id == 1 else self.km2
            return await km.check_key_status(slave_sae_id)
        except Exception as e:
            logger.error(f"Failed to check key status: {e}")
            # Return minimal status object
            return {"stored_key_count": 0, "error": str(e)}
    
    async def request_enc_keys(self, kme_id: int, slave_sae_id: int, number: int = 1) -> List[Dict[str, Any]]:
        """
        Request encryption keys with fallback to raw keys
        
        This method tries to get keys from OptimizedKMClient first,
        and if that fails, falls back to RealQKDClient raw keys
        """
        try:
            # First attempt to get keys from KME server
            logger.info(f"Attempting to get keys from KME {kme_id} server for SAE {slave_sae_id}")
            km = self.km1 if kme_id == 1 else self.km2
            keys = await km.request_enc_keys(slave_sae_id, number)
            logger.info(f"Successfully retrieved {len(keys)} keys from KME server")
            return keys
        except (KMConnectionError, InsufficientKeysError) as e:
            logger.warning(f"Failed to get keys from KME {kme_id} server: {e}, falling back to raw keys")
            
            # Fall back to raw keys
            real_km = self.real_km1 if kme_id == 1 else self.real_km2
            raw_keys = real_km.get_raw_keys(slave_sae_id, number)
            
            if not raw_keys:
                raise HybridKMError(f"No keys available from KME server and no raw keys available for fallback")
            
            # Convert raw keys to the format expected by encryption functions
            formatted_keys = []
            for i, key_data in enumerate(raw_keys):
                key_id = str(uuid.uuid4())
                key_b64 = base64.b64encode(key_data).decode('utf-8')
                
                formatted_keys.append({
                    "key_ID": key_id,
                    "key": key_b64,
                    "key_size": len(key_data) * 8
                })
            
            logger.info(f"Successfully retrieved {len(formatted_keys)} raw keys as fallback")
            return formatted_keys
        except Exception as e:
            logger.error(f"Failed to request encryption keys: {e}")
            raise HybridKMError(f"Failed to request encryption keys: {e}")
    
    async def request_dec_keys(self, kme_id: int, master_sae_id: int, key_ids: List[str]) -> List[Dict[str, Any]]:
        """Request decryption keys with fallback"""
        try:
            # Try to get keys from KME server first
            km = self.km1 if kme_id == 1 else self.km2
            keys = await km.request_dec_keys(master_sae_id, key_ids)
            
            # Add to consumed keys
            for key in keys:
                key_id = key.get("key_ID")
                if key_id:
                    self.consumed_keys.add(key_id)
            
            return keys
            
        except Exception as e:
            logger.warning(f"Failed to get decryption keys from KME server: {e}")
            
            # Raw key fallback only works if we generated the keys ourselves
            # Otherwise, we'd need to map key IDs to raw key files, which is not possible
            logger.error("Cannot fall back to raw keys for decryption - key IDs unknown")
            raise HybridKMError(f"Failed to get decryption keys: {e}")
    
    async def get_status(self, kme_id: int) -> Dict[str, Any]:
        """Get server status with fallback"""
        try:
            # Try optimized KM client first
            km = self.km1 if kme_id == 1 else self.km2
            status = await km.get_status()
            return status
        except Exception as e:
            logger.warning(f"Failed to get status from KME server: {e}, falling back to real client")
            
            # Fall back to real client
            real_km = self.real_km1 if kme_id == 1 else self.real_km2
            try:
                status = await real_km.get_real_status()
                return status
            except Exception as e2:
                logger.error(f"Failed to get status from real client: {e2}")
                return {"healthy": False, "error": str(e2)}
    
    async def check_entropy(self, kme_id: int) -> float:
        """Check entropy with fallback"""
        try:
            # Try optimized KM client first
            km = self.km1 if kme_id == 1 else self.km2
            return await km.check_entropy()
        except Exception as e:
            logger.warning(f"Failed to check entropy from KME server: {e}")
            
            # Return a conservative default
            return 7.5  # Default to reasonably good entropy
    
    def calculate_entropy(self, data: bytes) -> float:
        """Calculate Shannon entropy of data"""
        if not data:
            return 0.0
        
        import math
        byte_counts = [0] * 256
        for byte in data:
            byte_counts[byte] += 1
        
        entropy = 0.0
        length = len(data)
        
        for count in byte_counts:
            if count > 0:
                probability = count / length
                entropy -= probability * (math.log2(probability))
        
        return entropy

    async def get_hybrid_key(self, sender_kme_id: int, receiver_kme_id: int) -> Tuple[str, bytes]:
        """
        Get a quantum key using the hybrid approach
        
        1. Try to get a key from the KME servers
        2. If that fails, fall back to raw key files
        """
        try:
            # First try to get key from KME server
            km = self.km1 if sender_kme_id == 1 else self.km2
            
            # Determine the receiver SAE ID
            if sender_kme_id == 1:
                receiver_sae_id = 3  # KME 2 uses SAE ID 3
            else:
                receiver_sae_id = 1  # KME 1 uses SAE ID 1
            
            # Request encryption key
            keys = await self.request_enc_keys(sender_kme_id, receiver_sae_id, 1)
            
            if not keys:
                raise HybridKMError("No encryption keys available")
            
            key_data = keys[0]
            key_id = key_data.get("key_ID")
            key_b64 = key_data.get("key")
            
            if not key_id or not key_b64:
                raise HybridKMError("Invalid key data")
            
            # Decode the key from base64
            key_bytes = base64.b64decode(key_b64)
            
            # Log success
            logger.info(f"Successfully retrieved quantum key {key_id} with hybrid approach")
            
            return key_id, key_bytes
            
        except Exception as e:
            logger.error(f"Failed to get hybrid key: {e}")
            raise HybridKMError(f"Failed to get hybrid key: {e}")

# Create the singleton instance
hybrid_km_service = HybridKMService()
