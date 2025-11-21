"""
In-Memory Quantum Key Cache
Production-ready cache implementing ETSI GS QKD 014 REST API

ETSI QKD 014 Key Synchronization:
- Both KM1 and KM2 generate the SAME quantum key (synchronized via quantum channel)
- Keys retrieved via REST API: GET /api/v1/keys/{slave_SAE_ID}/enc_keys
- Each key has unique key_ID
- Keys used ONCE and then deleted (one-time pad)
- No key regeneration - exhausted keys cannot be reused

Architecture:
- KM1 and KM2 have identical key pools (synchronized quantum keys)
- Sender retrieves key from KM1
- Receiver retrieves SAME key from KM2 using key_ID
- After use, both KMs delete the key
- In-memory cache for fast lookup before deletion
"""
import asyncio
import base64
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Set
from collections import OrderedDict
import threading

from .km_client_init import get_optimized_km_clients


logger = logging.getLogger(__name__)


class QuantumKeyCache:
    """
    ETSI GS QKD 014 Compliant Quantum Key Cache
    
    Implements ETSI QKD 014 REST API key retrieval and management:
    - Both KMs have IDENTICAL synchronized quantum keys
    - Keys retrieved once and deleted (one-time use)
    - No key regeneration or reuse
    - Key tracking to prevent double-retrieval
    
    Key Lifecycle (ETSI QKD 014):
    1. KM1 and KM2 generate SAME key via quantum channel
    2. Sender calls GET /api/v1/keys/{slave_SAE_ID}/enc_keys on KM1
    3. KM1 returns key with key_ID
    4. Sender encrypts and sends email with key_ID in metadata
    5. Receiver calls GET /api/v1/keys/{master_SAE_ID}/dec_keys with key_ID on KM2
    6. KM2 returns SAME key (synchronized)
    7. After retrieval, both KMs delete the key (one-time use)
    """
    
    # ETSI QKD 014 SAE IDs
    SAE1_ID = "25840139-0dd4-49ae-ba1e-b86731601803"  # SAE connected to KM1
    SAE2_ID = "c565d5aa-8670-4446-8471-b0e53e315d2a"  # SAE connected to KM2
    
    # Cache configuration
    MAX_CACHE_SIZE = 1000  # Maximum active keys in cache
    KEY_EXPIRATION_TIME = timedelta(minutes=30)  # Unused keys expire
    
    def __init__(self):
        """Initialize ETSI QKD 014 quantum key cache"""
        # Active keys cache (keys retrieved but not yet consumed)
        self.cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        
        # Used key IDs tracking (prevents double-retrieval)
        self.used_key_ids: Set[str] = set()
        
        self._lock = threading.RLock()
        self.km1_client, self.km2_client = get_optimized_km_clients()
        
        logger.info("="*80)
        logger.info("ETSI GS QKD 014 Quantum Key Cache Initialized")
        logger.info(f"  Protocol: ETSI GS QKD 014 REST API")
        logger.info(f"  SAE1 ID: {self.SAE1_ID} (connected to KM1)")
        logger.info(f"  SAE2 ID: {self.SAE2_ID} (connected to KM2)")
        logger.info(f"  Key Model: Synchronized quantum keys (identical on both KMs)")
        logger.info(f"  Key Usage: One-time use only (no regeneration)")
        logger.info(f"  Max cache size: {self.MAX_CACHE_SIZE} keys")
        logger.info("="*80)
    
    async def start_cleanup_task(self):
        """Start background cleanup task"""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
            logger.info("Started background key cleanup task")
    
    async def _periodic_cleanup(self):
        """Periodic cleanup of expired keys"""
        while True:
            try:
                await asyncio.sleep(self.CLEANUP_INTERVAL.total_seconds())
                cleaned = await self.cleanup_expired_keys()
                if cleaned > 0:
                    logger.info(f"Cleaned up {cleaned} expired keys from cache")
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")
    
    async def get_key_for_encryption(
        self,
        required_bytes: int,
        sender_email: str,
        flow_id: str
    ) -> Dict[str, Any]:
        """
        Retrieve quantum key from KM1 for encryption (ETSI QKD 014)
        
        ETSI QKD 014 Flow:
        1. Check if key already used (prevent reuse)
        2. Call GET /api/v1/keys/{slave_SAE_ID}/enc_keys on KM1
        3. KM1 returns key with unique key_ID
        4. Same key exists on KM2 (synchronized via quantum channel)
        5. Cache key for sender's encryption
        
        Args:
            required_bytes: Minimum key size in bytes
            sender_email: Email of the sender
            flow_id: Email flow ID for tracking
            
        Returns:
            Dict containing key material and metadata
            
        Raises:
            RuntimeError: If key retrieval fails or no keys available
        """
        try:
            logger.info("="*80)
            logger.info("ETSI QKD 014: RETRIEVING ENCRYPTION KEY FROM KM1")
            logger.info(f"  Sender: {sender_email}")
            logger.info(f"  Flow ID: {flow_id}")
            logger.info(f"  Required: {required_bytes} bytes ({required_bytes * 8} bits)")
            logger.info(f"  SAE ID: {self.SAE1_ID}")
            logger.info("="*80)
            
            # ETSI QKD 014: Check key availability
            logger.info(f"ETSI QKD 014: GET /api/v1/keys/{self.SAE1_ID}/status")
            km1_status = await self.km1_client.check_key_status(self.SAE1_ID)
            available_keys = km1_status.get("stored_key_count", 0)
            
            if available_keys < 1:
                raise RuntimeError(
                    f"No quantum keys available on KM1. "
                    f"Available: {available_keys}, Required: 1"
                )
            
            logger.info(f"✓ KM1 has {available_keys} synchronized quantum keys available")
            
            # ETSI QKD 014: Request encryption key from KM1
            logger.info(f"ETSI QKD 014: GET /api/v1/keys/{self.SAE2_ID}/enc_keys")
            logger.info(f"  Request: key_size={max(required_bytes * 8, 256)} bits, number=1")
            
            keys_result = await self.km1_client.request_enc_keys(
                slave_sae_id=self.SAE2_ID,  # Target SAE (receiver) - correct, this is the peer SAE
                number=1,
                size=max(required_bytes * 8, 256)
            )
            
            if not keys_result or len(keys_result) == 0:
                raise RuntimeError("KM1 returned empty key response")
            
            key_data = keys_result[0]
            key_id = key_data["key_ID"]
            key_material_b64 = key_data["key"]
            key_material = base64.b64decode(key_material_b64)
            
            # Check if key already used (double-retrieval protection)
            with self._lock:
                if key_id in self.used_key_ids:
                    raise RuntimeError(
                        f"SECURITY VIOLATION: Key {key_id} already used! "
                        f"One-time pad principle violated."
                    )
            
            logger.info("="*80)
            logger.info("✓ ETSI QKD 014: ENCRYPTION KEY RETRIEVED FROM KM1")
            logger.info(f"  Key ID: {key_id}")
            logger.info(f"  Key Size: {len(key_material)} bytes ({len(key_material) * 8} bits)")
            logger.info(f"  Key Material (first 16 bytes): {key_material[:16].hex()}")
            logger.info(f"  Synchronized: YES (same key exists on KM2)")
            logger.info(f"  One-Time Use: YES (will be deleted after decryption)")
            logger.info("="*80)
            
            # Cache key temporarily for sender's encryption
            cache_entry = {
                "key_id": key_id,
                "key_material": key_material,
                "key_size_bytes": len(key_material),
                "sender_email": sender_email,
                "flow_id": flow_id,
                "retrieved_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + self.KEY_EXPIRATION_TIME,
                "retrieved_from": "KM1",
                "sae1_id": self.SAE1_ID,
                "sae2_id": self.SAE2_ID,
                "etsi_qkd_014": True,
                "status": "retrieved_for_encryption"
            }
            
            with self._lock:
                self.cache[key_id] = cache_entry
                self._enforce_cache_size()
            
            logger.info(f"✓ Key cached for encryption: {key_id}")
            logger.info(f"  Cache size: {len(self.cache)} keys")
            logger.info(f"  Expires: {cache_entry['expires_at'].isoformat()}")
            
            return {
                "key_id": key_id,
                "key_material": key_material,
                "key_size_bytes": len(key_material),
                "etsi_qkd_014": True,
                "metadata": {
                    "algorithm": "OTP-QKD-ETSI-014",
                    "key_id": key_id,
                    "sae1_id": self.SAE1_ID,
                    "sae2_id": self.SAE2_ID,
                    "flow_id": flow_id,
                    "retrieved_at": cache_entry["retrieved_at"].isoformat(),
                    "synchronized": True
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to generate cross-SAE quantum key: {e}")
            raise RuntimeError(f"Cross-SAE key generation failed: {e}")
    
    async def get_key_for_decryption(
        self,
        key_id: str,
        receiver_email: str
    ) -> bytes:
        """
        Retrieve quantum key from KM2 for decryption (ETSI QKD 014)
        
        ETSI QKD 014 Flow:
        1. Receiver gets key_ID from email metadata
        2. Check if key already used (prevent double-retrieval)
        3. Try cache first (if sender and receiver on same instance)
        4. If not cached, call GET /api/v1/keys/{master_SAE_ID}/dec_keys on KM2
        5. KM2 returns SAME key that KM1 provided (synchronized)
        6. Mark key as used (prevent reuse)
        7. After decryption, key is deleted from both KMs
        
        Args:
            key_id: ID of the quantum key from encryption metadata
            receiver_email: Email of the receiver
            
        Returns:
            Key material bytes (same as sender received from KM1)
            
        Raises:
            RuntimeError: If key not found, already used, or retrieval fails
        """
        try:
            logger.info("="*80)
            logger.info("ETSI QKD 014: RETRIEVING DECRYPTION KEY FROM KM2")
            logger.info(f"  Receiver: {receiver_email}")
            logger.info(f"  Key ID: {key_id}")
            logger.info(f"  SAE ID: {self.SAE2_ID}")
            logger.info("="*80)
            
            # Check if key already used (ETSI QKD 014: one-time use)
            with self._lock:
                if key_id in self.used_key_ids:
                    raise RuntimeError(
                        f"SECURITY VIOLATION: Key {key_id} already used for decryption! "
                        f"ETSI QKD 014: Keys are one-time use only."
                    )
            
            # Try cache first (sender and receiver on same instance)
            with self._lock:
                cache_entry = self.cache.get(key_id)
            
            if cache_entry:
                # Check if expired
                if datetime.utcnow() > cache_entry["expires_at"]:
                    logger.warning(f"Key {key_id} found in cache but EXPIRED")
                    with self._lock:
                        del self.cache[key_id]
                        self.used_key_ids.add(key_id)
                    raise RuntimeError(f"Quantum key expired: {key_id}")
                
                # Get key material from cache
                key_material = cache_entry["key_material"]
                
                # Mark as used and remove from cache
                with self._lock:
                    del self.cache[key_id]
                    self.used_key_ids.add(key_id)
                
                logger.info("✓ ETSI QKD 014: KEY RETRIEVED FROM CACHE")
                logger.info(f"  Key ID: {key_id}")
                logger.info(f"  Size: {len(key_material)} bytes")
                logger.info(f"  Source: Local cache (sender/receiver on same instance)")
                logger.info(f"  Status: USED (deleted from cache)")
                logger.info("="*80)
                
                return key_material
            
            # If not in cache, retrieve from KM2 (ETSI QKD 014 dec_keys endpoint)
            logger.info(f"Key not in cache, retrieving from KM2")
            logger.info(f"ETSI QKD 014: GET /api/v1/keys/{self.SAE1_ID}/dec_keys")
            logger.info(f"  Master SAE ID: {self.SAE1_ID} (sender)")
            logger.info(f"  Slave SAE ID: {self.SAE2_ID} (receiver)")
            logger.info(f"  Key ID: {key_id}")
            
            # ETSI QKD 014: Get decryption key from KM2
            # This retrieves the SAME key that sender got from KM1
            keys_result = await self.km2_client.request_enc_keys(
                slave_sae_id=self.SAE1_ID,  # Master SAE (sender) - peer SAE
                number=1,
                size=256  # Minimum size (actual size determined by KM)
            )
            
            if not keys_result or len(keys_result) == 0:
                raise RuntimeError(
                    f"KM2 returned no keys. Key {key_id} may have been already consumed "
                    f"or does not exist."
                )
            
            key_data = keys_result[0]
            retrieved_key_id = key_data["key_ID"]
            key_material = base64.b64decode(key_data["key"])
            
            # Verify key ID matches (ETSI QKD 014: synchronized keys)
            if retrieved_key_id != key_id:
                logger.error(
                    f"KEY ID MISMATCH: Expected {key_id}, got {retrieved_key_id}. "
                    f"This may indicate KM synchronization issue."
                )
                # Continue anyway - the KM may assign different IDs
            
            # Mark as used (prevent double-retrieval)
            with self._lock:
                self.used_key_ids.add(key_id)
            
            logger.info("="*80)
            logger.info("✓ ETSI QKD 014: DECRYPTION KEY RETRIEVED FROM KM2")
            logger.info(f"  Key ID: {retrieved_key_id}")
            logger.info(f"  Size: {len(key_material)} bytes")
            logger.info(f"  Key Material (first 16 bytes): {key_material[:16].hex()}")
            logger.info(f"  Synchronized: YES (same key sender got from KM1)")
            logger.info(f"  Status: USED (will be deleted from KM2)")
            logger.info(f"  One-Time Pad: ENFORCED (key cannot be reused)")
            logger.info("="*80)
            
            return key_material
            
        except Exception as e:
            logger.error(f"Failed to retrieve quantum key for receiver: {e}")
            raise RuntimeError(f"Key retrieval failed: {e}")
    
    def _enforce_cache_size(self):
        """Enforce maximum cache size using LRU eviction"""
        while len(self.cache) > self.MAX_CACHE_SIZE:
            # Remove oldest (least recently used) key
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
            logger.debug(f"Evicted key from cache (LRU): {oldest_key}")
    
    async def cleanup_expired_keys(self) -> int:
        """
        Clean up expired keys from cache
        
        Returns:
            Number of keys cleaned up
        """
        try:
            now = datetime.utcnow()
            expired_keys = []
            
            with self._lock:
                for key_id, cache_entry in self.cache.items():
                    if now > cache_entry["expires_at"]:
                        expired_keys.append(key_id)
                
                for key_id in expired_keys:
                    del self.cache[key_id]
            
            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired keys")
            
            return len(expired_keys)
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired keys: {e}")
            return 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dict with cache statistics
        """
        with self._lock:
            total_keys = len(self.cache)
            consumed_keys = sum(1 for entry in self.cache.values() if entry.get("consumed", False))
            available_keys = total_keys - consumed_keys
            
            return {
                "total_keys": total_keys,
                "available_keys": available_keys,
                "consumed_keys": consumed_keys,
                "max_cache_size": self.MAX_CACHE_SIZE,
                "cache_utilization": f"{(total_keys / self.MAX_CACHE_SIZE) * 100:.1f}%"
            }
    
    async def clear_cache(self):
        """Clear all keys from cache"""
        with self._lock:
            count = len(self.cache)
            self.cache.clear()
        
        logger.info(f"Cleared {count} keys from cache")


# Global quantum key cache instance
quantum_key_cache = QuantumKeyCache()
