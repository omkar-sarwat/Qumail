"""
Local Key Manager (LKM) for QuMail
==================================

This module provides a local key storage system that:
1. Fetches quantum keys from main KME servers and stores locally
2. Serves keys to application from local storage (fast)
3. Falls back to main KME if local storage is empty
4. Auto-fills local cache by periodically fetching from main KME
5. Persists keys to SQLite for durability across restarts

Architecture:
    Main KME (KM1/KM2) --fetch--> Local Key Manager --serve--> Application
                                        |
                                    SQLite DB
                                        |
                                    Persistent Storage

Key Flow:
1. Background service fetches keys from main KME periodically
2. Keys stored in SQLite with metadata (key_id, key_material, source, etc.)
3. Application requests key -> LKM serves from local first
4. If local empty -> LKM fetches from main KME directly
5. Used keys are marked as consumed and deleted

ETSI QKD 014 Compliance:
- Keys are one-time use only
- Key IDs are unique and tracked
- Synchronized keys work across KM1/KM2
"""

import asyncio
import base64
import logging
import sqlite3
import threading
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from contextlib import contextmanager
import json

logger = logging.getLogger(__name__)


class LocalKeyManagerConfig:
    """Configuration for Local Key Manager"""
    
    # Database settings
    DB_PATH = Path(__file__).parent.parent.parent / "data" / "local_keys.db"
    
    # Key pool settings
    MIN_KEYS_THRESHOLD = 5  # Fetch more keys when pool drops below this
    MAX_KEYS_TO_STORE = 50  # Maximum keys to store locally
    KEYS_PER_FETCH = 10  # Number of keys to fetch at once (initial: 10 keys)
    
    # Auto-fill settings
    AUTO_FILL_ENABLED = True
    AUTO_FILL_INTERVAL_SECONDS = 30  # Check every 30 seconds
    
    # Key expiration
    KEY_EXPIRATION_HOURS = 24  # Keys expire after 24 hours
    
    # Default key sizes
    DEFAULT_KEY_SIZE_BITS = 256
    
    # SAE IDs (from ETSI QKD 014)
    SAE1_ID = "25840139-0dd4-49ae-ba1e-b86731601803"
    SAE2_ID = "c565d5aa-8670-4446-8471-b0e53e315d2a"


class LocalKeyManager:
    """
    Local Key Manager - Stores and manages quantum keys locally
    
    Features:
    - SQLite-based persistent storage
    - Auto-fill from main KME servers
    - Fast local key retrieval
    - Fallback to main KME when local is empty
    - Thread-safe operations
    - Key expiration handling
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern for Local Key Manager"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.config = LocalKeyManagerConfig()
        self._db_lock = threading.RLock()
        self._auto_fill_task: Optional[asyncio.Task] = None
        self._km_clients_initialized = False
        self._km1_client = None
        self._km2_client = None
        
        # Initialize database
        self._init_database()
        
        self._initialized = True
        
        logger.info("="*80)
        logger.info("LOCAL KEY MANAGER INITIALIZED")
        logger.info(f"  Database: {self.config.DB_PATH}")
        logger.info(f"  Min Keys Threshold: {self.config.MIN_KEYS_THRESHOLD}")
        logger.info(f"  Max Keys to Store: {self.config.MAX_KEYS_TO_STORE}")
        logger.info(f"  Auto-fill Enabled: {self.config.AUTO_FILL_ENABLED}")
        logger.info(f"  Auto-fill Interval: {self.config.AUTO_FILL_INTERVAL_SECONDS}s")
        logger.info("="*80)
    
    def _init_database(self):
        """Initialize SQLite database for key storage"""
        # Ensure data directory exists
        self.config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Create keys table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS quantum_keys (
                    key_id TEXT PRIMARY KEY,
                    key_material BLOB NOT NULL,
                    key_size_bytes INTEGER NOT NULL,
                    source TEXT NOT NULL,  -- 'KM1' or 'KM2'
                    sae1_id TEXT,
                    sae2_id TEXT,
                    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    status TEXT DEFAULT 'available',  -- 'available', 'reserved', 'consumed'
                    reserved_for TEXT,  -- flow_id if reserved
                    consumed_at TIMESTAMP,
                    metadata TEXT  -- JSON metadata
                )
            """)
            
            # Create index for fast lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_keys_status 
                ON quantum_keys(status, expires_at)
            """)
            
            # Create usage log table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS key_usage_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key_id TEXT NOT NULL,
                    action TEXT NOT NULL,  -- 'fetched', 'served', 'consumed', 'expired'
                    details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create statistics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS lkm_statistics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stat_type TEXT NOT NULL,
                    stat_value INTEGER DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            logger.info(f"Database initialized at {self.config.DB_PATH}")
    
    @contextmanager
    def _get_db_connection(self):
        """Get database connection with thread safety"""
        conn = sqlite3.connect(
            str(self.config.DB_PATH),
            timeout=30.0,
            check_same_thread=False
        )
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def _init_km_clients(self):
        """Initialize KM clients lazily"""
        if not self._km_clients_initialized:
            try:
                from .km_client_init import get_optimized_km_clients
                self._km1_client, self._km2_client = get_optimized_km_clients()
                self._km_clients_initialized = True
                logger.info("KM clients initialized for Local Key Manager")
            except Exception as e:
                logger.warning(f"Could not initialize KM clients: {e}")
    
    # ==================== KEY STORAGE OPERATIONS ====================
    
    def get_available_key_count(self) -> int:
        """Get count of available (non-expired, non-consumed) keys"""
        with self._db_lock:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) FROM quantum_keys 
                    WHERE status = 'available' 
                    AND (expires_at IS NULL OR expires_at > datetime('now'))
                """)
                return cursor.fetchone()[0]
    
    def get_key_statistics(self) -> Dict[str, Any]:
        """Get comprehensive key statistics"""
        with self._db_lock:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Total keys
                cursor.execute("SELECT COUNT(*) FROM quantum_keys")
                total = cursor.fetchone()[0]
                
                # Available keys
                cursor.execute("""
                    SELECT COUNT(*) FROM quantum_keys 
                    WHERE status = 'available' 
                    AND (expires_at IS NULL OR expires_at > datetime('now'))
                """)
                available = cursor.fetchone()[0]
                
                # Consumed keys
                cursor.execute("SELECT COUNT(*) FROM quantum_keys WHERE status = 'consumed'")
                consumed = cursor.fetchone()[0]
                
                # Expired keys
                cursor.execute("""
                    SELECT COUNT(*) FROM quantum_keys 
                    WHERE expires_at <= datetime('now') AND status != 'consumed'
                """)
                expired = cursor.fetchone()[0]
                
                # Keys by source
                cursor.execute("""
                    SELECT source, COUNT(*) FROM quantum_keys 
                    WHERE status = 'available'
                    GROUP BY source
                """)
                by_source = dict(cursor.fetchall())
                
                return {
                    "total_keys": total,
                    "available_keys": available,
                    "consumed_keys": consumed,
                    "expired_keys": expired,
                    "keys_by_source": by_source,
                    "min_threshold": self.config.MIN_KEYS_THRESHOLD,
                    "max_capacity": self.config.MAX_KEYS_TO_STORE,
                    "needs_refill": available < self.config.MIN_KEYS_THRESHOLD
                }
    
    def store_key(
        self,
        key_id: str,
        key_material: bytes,
        source: str,
        sae1_id: str = None,
        sae2_id: str = None,
        metadata: Dict = None
    ) -> bool:
        """Store a quantum key in local storage"""
        try:
            expires_at = datetime.utcnow() + timedelta(hours=self.config.KEY_EXPIRATION_HOURS)
            
            with self._db_lock:
                with self._get_db_connection() as conn:
                    cursor = conn.cursor()
                    
                    # Check if key already exists
                    cursor.execute("SELECT key_id FROM quantum_keys WHERE key_id = ?", (key_id,))
                    if cursor.fetchone():
                        logger.warning(f"Key {key_id} already exists in local storage")
                        return False
                    
                    # Check capacity
                    cursor.execute("SELECT COUNT(*) FROM quantum_keys WHERE status = 'available'")
                    current_count = cursor.fetchone()[0]
                    
                    if current_count >= self.config.MAX_KEYS_TO_STORE:
                        logger.warning(f"Local key storage at capacity ({current_count}/{self.config.MAX_KEYS_TO_STORE})")
                        return False
                    
                    # Store key
                    cursor.execute("""
                        INSERT INTO quantum_keys 
                        (key_id, key_material, key_size_bytes, source, sae1_id, sae2_id, 
                         expires_at, status, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 'available', ?)
                    """, (
                        key_id,
                        key_material,
                        len(key_material),
                        source,
                        sae1_id or self.config.SAE1_ID,
                        sae2_id or self.config.SAE2_ID,
                        expires_at.isoformat(),
                        json.dumps(metadata) if metadata else None
                    ))
                    
                    # Log the action
                    cursor.execute("""
                        INSERT INTO key_usage_log (key_id, action, details)
                        VALUES (?, 'stored', ?)
                    """, (key_id, f"Stored from {source}, expires {expires_at.isoformat()}"))
                    
                    conn.commit()
                    
            logger.info(f"✓ Stored key {key_id[:16]}... from {source} (expires {expires_at.isoformat()})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store key: {e}")
            return False
    
    def get_local_key(self, required_bytes: int = 32) -> Optional[Dict[str, Any]]:
        """
        Get a key from local storage
        
        Args:
            required_bytes: Minimum key size needed
            
        Returns:
            Key data dict or None if no suitable key available
        """
        try:
            with self._db_lock:
                with self._get_db_connection() as conn:
                    cursor = conn.cursor()
                    
                    # Find available key with sufficient size
                    cursor.execute("""
                        SELECT key_id, key_material, key_size_bytes, source, 
                               sae1_id, sae2_id, fetched_at, metadata
                        FROM quantum_keys 
                        WHERE status = 'available' 
                        AND key_size_bytes >= ?
                        AND (expires_at IS NULL OR expires_at > datetime('now'))
                        ORDER BY fetched_at ASC
                        LIMIT 1
                    """, (required_bytes,))
                    
                    row = cursor.fetchone()
                    
                    if not row:
                        logger.warning(f"No local key available with size >= {required_bytes} bytes")
                        return None
                    
                    key_id = row['key_id']
                    
                    # Mark as reserved temporarily (will be consumed after use)
                    cursor.execute("""
                        UPDATE quantum_keys 
                        SET status = 'reserved'
                        WHERE key_id = ?
                    """, (key_id,))
                    
                    # Log the action
                    cursor.execute("""
                        INSERT INTO key_usage_log (key_id, action, details)
                        VALUES (?, 'served', 'Served from local storage')
                    """, (key_id,))
                    
                    conn.commit()
                    
            logger.info(f"✓ Serving local key {key_id[:16]}... ({row['key_size_bytes']} bytes)")
            
            metadata = json.loads(row['metadata']) if row['metadata'] else {}
            
            return {
                "key_id": key_id,
                "key_material": row['key_material'],
                "key_size_bytes": row['key_size_bytes'],
                "source": row['source'],
                "sae1_id": row['sae1_id'],
                "sae2_id": row['sae2_id'],
                "fetched_at": row['fetched_at'],
                "from_local": True,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Failed to get local key: {e}")
            return None
    
    def get_key_by_id(self, key_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific key by ID (for decryption)"""
        try:
            with self._db_lock:
                with self._get_db_connection() as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        SELECT key_id, key_material, key_size_bytes, source,
                               sae1_id, sae2_id, status, metadata
                        FROM quantum_keys 
                        WHERE key_id = ?
                    """, (key_id,))
                    
                    row = cursor.fetchone()
                    
                    if not row:
                        return None
                    
                    if row['status'] == 'consumed':
                        logger.warning(f"Key {key_id} already consumed!")
                        return None
                    
                    metadata = json.loads(row['metadata']) if row['metadata'] else {}
                    
                    return {
                        "key_id": key_id,
                        "key_material": row['key_material'],
                        "key_size_bytes": row['key_size_bytes'],
                        "source": row['source'],
                        "sae1_id": row['sae1_id'],
                        "sae2_id": row['sae2_id'],
                        "from_local": True,
                        "metadata": metadata
                    }
                    
        except Exception as e:
            logger.error(f"Failed to get key by ID: {e}")
            return None
    
    def consume_key(self, key_id: str) -> bool:
        """Mark a key as consumed (one-time use)"""
        try:
            with self._db_lock:
                with self._get_db_connection() as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        UPDATE quantum_keys 
                        SET status = 'consumed', consumed_at = datetime('now')
                        WHERE key_id = ?
                    """, (key_id,))
                    
                    cursor.execute("""
                        INSERT INTO key_usage_log (key_id, action, details)
                        VALUES (?, 'consumed', 'Key consumed after use')
                    """, (key_id,))
                    
                    conn.commit()
                    
            logger.info(f"✓ Key {key_id[:16]}... marked as consumed")
            return True
            
        except Exception as e:
            logger.error(f"Failed to consume key: {e}")
            return False
    
    def cleanup_expired_keys(self) -> int:
        """Remove expired and consumed keys from storage"""
        try:
            with self._db_lock:
                with self._get_db_connection() as conn:
                    cursor = conn.cursor()
                    
                    # Delete expired keys
                    cursor.execute("""
                        DELETE FROM quantum_keys 
                        WHERE expires_at <= datetime('now')
                        OR status = 'consumed'
                    """)
                    
                    deleted = cursor.rowcount
                    conn.commit()
                    
            if deleted > 0:
                logger.info(f"Cleaned up {deleted} expired/consumed keys")
            return deleted
            
        except Exception as e:
            logger.error(f"Failed to cleanup keys: {e}")
            return 0
    
    # ==================== KEY FETCHING FROM MAIN KME ====================
    
    async def fetch_keys_from_main_kme(self, count: int = None) -> int:
        """
        Fetch quantum keys from main KME servers and store locally
        
        Args:
            count: Number of keys to fetch (default: KEYS_PER_FETCH)
            
        Returns:
            Number of keys successfully fetched and stored
        """
        count = count or self.config.KEYS_PER_FETCH
        
        # Initialize KM clients if needed
        self._init_km_clients()
        
        if not self._km1_client:
            logger.warning("KM1 client not available, cannot fetch keys")
            return 0
        
        fetched_count = 0
        
        logger.info("="*60)
        logger.info(f"FETCHING {count} KEYS FROM MAIN KME...")
        logger.info("="*60)
        
        try:
            # Check current capacity
            available = self.get_available_key_count()
            space_available = self.config.MAX_KEYS_TO_STORE - available
            
            if space_available <= 0:
                logger.info(f"Local storage full ({available}/{self.config.MAX_KEYS_TO_STORE})")
                return 0
            
            # Limit to available space
            count = min(count, space_available)
            
            # Try to fetch from KM1
            for i in range(count):
                try:
                    # Request key from KM1
                    keys_result = await self._km1_client.request_enc_keys(
                        slave_sae_id=self.config.SAE2_ID,
                        number=1,
                        size=self.config.DEFAULT_KEY_SIZE_BITS
                    )
                    
                    if keys_result and len(keys_result) > 0:
                        key_data = keys_result[0]
                        key_id = key_data["key_ID"]
                        key_material = base64.b64decode(key_data["key"])
                        
                        # Store locally
                        if self.store_key(
                            key_id=key_id,
                            key_material=key_material,
                            source="KM1",
                            metadata={"fetched_from": "main_kme", "batch": i + 1}
                        ):
                            fetched_count += 1
                        
                except Exception as e:
                    logger.warning(f"Failed to fetch key {i+1}: {e}")
                    # Don't break on individual failures
                    continue
            
            logger.info(f"✓ Fetched {fetched_count}/{count} keys from main KME")
            
        except Exception as e:
            logger.error(f"Error fetching keys from main KME: {e}")
        
        return fetched_count
    
    async def ensure_minimum_keys(self) -> bool:
        """Ensure we have at least the minimum number of keys"""
        available = self.get_available_key_count()
        
        if available >= self.config.MIN_KEYS_THRESHOLD:
            return True
        
        needed = self.config.MIN_KEYS_THRESHOLD - available
        logger.info(f"Key pool low ({available}/{self.config.MIN_KEYS_THRESHOLD}), fetching {needed} more...")
        
        fetched = await self.fetch_keys_from_main_kme(needed)
        
        return fetched > 0
    
    # ==================== AUTO-FILL SERVICE ====================
    
    async def start_auto_fill_service(self):
        """Start background service that auto-fills key pool"""
        if not self.config.AUTO_FILL_ENABLED:
            logger.info("Auto-fill service disabled")
            return
        
        if self._auto_fill_task is not None:
            logger.warning("Auto-fill service already running")
            return
        
        self._auto_fill_task = asyncio.create_task(self._auto_fill_loop())
        logger.info(f"✓ Auto-fill service started (interval: {self.config.AUTO_FILL_INTERVAL_SECONDS}s)")
    
    async def stop_auto_fill_service(self):
        """Stop the auto-fill background service"""
        if self._auto_fill_task:
            self._auto_fill_task.cancel()
            try:
                await self._auto_fill_task
            except asyncio.CancelledError:
                pass
            self._auto_fill_task = None
            logger.info("Auto-fill service stopped")
    
    async def _auto_fill_loop(self):
        """Background loop that maintains minimum key count"""
        while True:
            try:
                # Cleanup expired keys first
                self.cleanup_expired_keys()
                
                # Get current stats
                stats = self.get_key_statistics()
                available = stats["available_keys"]
                
                logger.info(f"[Auto-fill] Available keys: {available}/{self.config.MAX_KEYS_TO_STORE}")
                
                # Check if we need to refill
                if available < self.config.MIN_KEYS_THRESHOLD:
                    logger.info(f"[Auto-fill] Key pool low, fetching more keys...")
                    await self.fetch_keys_from_main_kme()
                
                # Wait for next interval
                await asyncio.sleep(self.config.AUTO_FILL_INTERVAL_SECONDS)
                
            except asyncio.CancelledError:
                logger.info("Auto-fill loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in auto-fill loop: {e}")
                await asyncio.sleep(10)  # Wait before retry
    
    # ==================== UNIFIED KEY RETRIEVAL ====================
    
    async def get_encryption_key(
        self,
        required_bytes: int = 32,
        sender_email: str = "",
        flow_id: str = ""
    ) -> Dict[str, Any]:
        """
        Get a quantum key for encryption
        
        Priority:
        1. Try local storage first (fast)
        2. If local empty, fetch from main KME
        
        Args:
            required_bytes: Minimum key size in bytes
            sender_email: Email of sender (for logging)
            flow_id: Flow ID for tracking
            
        Returns:
            Key data dict with key_id, key_material, metadata
        """
        logger.info("="*60)
        logger.info("LOCAL KEY MANAGER: GET ENCRYPTION KEY")
        logger.info(f"  Required: {required_bytes} bytes")
        logger.info(f"  Sender: {sender_email}")
        logger.info(f"  Flow ID: {flow_id}")
        logger.info("="*60)
        
        # First, try local storage
        local_key = self.get_local_key(required_bytes)
        
        if local_key:
            logger.info(f"✓ USING LOCAL KEY: {local_key['key_id'][:16]}...")
            logger.info(f"  Source: Local Storage")
            logger.info(f"  Original Source: {local_key['source']}")
            logger.info(f"  Size: {local_key['key_size_bytes']} bytes")
            
            return {
                "key_id": local_key["key_id"],
                "key_material": local_key["key_material"],
                "key_size_bytes": local_key["key_size_bytes"],
                "from_local": True,
                "etsi_qkd_014": True,
                "metadata": {
                    "algorithm": "OTP-QKD-ETSI-014",
                    "key_id": local_key["key_id"],
                    "sae1_id": local_key["sae1_id"],
                    "sae2_id": local_key["sae2_id"],
                    "flow_id": flow_id,
                    "source": "local_key_manager",
                    "original_source": local_key["source"]
                }
            }
        
        # Local empty, fallback to main KME
        logger.warning("Local key storage empty, falling back to main KME...")
        
        self._init_km_clients()
        
        if not self._km1_client:
            raise RuntimeError("No keys available in local storage and main KME unavailable")
        
        try:
            # Fetch directly from main KME
            keys_result = await self._km1_client.request_enc_keys(
                slave_sae_id=self.config.SAE2_ID,
                number=1,
                size=max(required_bytes * 8, self.config.DEFAULT_KEY_SIZE_BITS)
            )
            
            if not keys_result or len(keys_result) == 0:
                raise RuntimeError("Main KME returned empty key response")
            
            key_data = keys_result[0]
            key_id = key_data["key_ID"]
            key_material = base64.b64decode(key_data["key"])
            
            # Store in local for potential decryption later
            self.store_key(
                key_id=key_id,
                key_material=key_material,
                source="KM1",
                metadata={"flow_id": flow_id, "direct_fetch": True}
            )
            
            logger.info(f"✓ FETCHED KEY FROM MAIN KME: {key_id[:16]}...")
            
            return {
                "key_id": key_id,
                "key_material": key_material,
                "key_size_bytes": len(key_material),
                "from_local": False,
                "etsi_qkd_014": True,
                "metadata": {
                    "algorithm": "OTP-QKD-ETSI-014",
                    "key_id": key_id,
                    "sae1_id": self.config.SAE1_ID,
                    "sae2_id": self.config.SAE2_ID,
                    "flow_id": flow_id,
                    "source": "main_kme_direct"
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get key from main KME: {e}")
            raise RuntimeError(f"No keys available locally or from main KME: {e}")
    
    async def get_decryption_key(self, key_id: str, receiver_email: str = "") -> bytes:
        """
        Get a quantum key for decryption
        
        Priority:
        1. Try local storage first (key may have been pre-fetched)
        2. If not local, fetch from KM2
        
        Args:
            key_id: Key ID from encryption metadata
            receiver_email: Email of receiver (for logging)
            
        Returns:
            Key material bytes
        """
        logger.info("="*60)
        logger.info("LOCAL KEY MANAGER: GET DECRYPTION KEY")
        logger.info(f"  Key ID: {key_id}")
        logger.info(f"  Receiver: {receiver_email}")
        logger.info("="*60)
        
        # First, try local storage
        local_key = self.get_key_by_id(key_id)
        
        if local_key:
            key_material = local_key["key_material"]
            
            # Mark as consumed (one-time use)
            self.consume_key(key_id)
            
            logger.info(f"✓ USING LOCAL KEY FOR DECRYPTION: {key_id[:16]}...")
            logger.info(f"  Source: Local Storage")
            logger.info(f"  Size: {len(key_material)} bytes")
            
            return key_material
        
        # Not in local, try main KME (KM2 for decryption)
        logger.warning(f"Key {key_id} not in local storage, fetching from KM2...")
        
        self._init_km_clients()
        
        if not self._km2_client:
            raise RuntimeError(f"Key {key_id} not found locally and KM2 unavailable")
        
        try:
            # Fetch from KM2 using dec_keys endpoint
            key_material = await self._km2_client.request_dec_key(
                master_sae_id=self.config.SAE1_ID,
                key_id=key_id
            )
            
            if not key_material:
                raise RuntimeError(f"KM2 returned empty key for ID {key_id}")
            
            logger.info(f"✓ FETCHED KEY FROM KM2: {key_id[:16]}...")
            logger.info(f"  Size: {len(key_material)} bytes")
            
            return key_material
            
        except Exception as e:
            logger.error(f"Failed to get key from KM2: {e}")
            raise RuntimeError(f"Key {key_id} not found locally or on KM2: {e}")


# Global instance getter
_local_key_manager: Optional[LocalKeyManager] = None

def get_local_key_manager() -> LocalKeyManager:
    """Get the singleton Local Key Manager instance"""
    global _local_key_manager
    if _local_key_manager is None:
        _local_key_manager = LocalKeyManager()
    return _local_key_manager


async def initialize_local_key_manager() -> LocalKeyManager:
    """Initialize and start the Local Key Manager with auto-fill"""
    lkm = get_local_key_manager()
    await lkm.start_auto_fill_service()
    return lkm
