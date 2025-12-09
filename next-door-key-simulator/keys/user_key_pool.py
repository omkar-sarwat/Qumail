"""
Per-User Key Pool Management for ETSI GS QKD 014 Compliant QKD System

This module implements isolated per-user key pools where:
- Each user (identified by SAE_ID) has their own separate key pool
- Keys are exactly 1KB (1024 bytes) in size
- Sender requests keys FROM receiver's pool (not sender's own pool)
- One-time use enforcement (keys marked as used after delivery)
"""
import os
import json
import time
import secrets
import base64
import threading
import sqlite3
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
from pathlib import Path


# Key size constant: 1KB = 1024 bytes (standard quantum key size)
KEY_SIZE_BYTES = 1024
KEY_SIZE_BITS = KEY_SIZE_BYTES * 8


class UserKeyPool:
    """
    Manages per-user quantum key pools following ETSI GS QKD 014 standards.
    
    Each user has:
    - Unique SAE_ID (Secure Application Entity ID)
    - Isolated key pool (no sharing between users)
    - Keys of exactly 1KB (1024 bytes)
    - Metadata tracking (total, used, available keys)
    """
    
    def __init__(self, db_path: str = "user_key_pools.db"):
        """
        Initialize the User Key Pool manager.
        
        Args:
            db_path: Path to SQLite database for persistent storage
        """
        self.db_path = db_path
        self.lock = threading.RLock()
        self._init_database()
        print(f"[USER_KEY_POOL] Initialized with database: {db_path}")
    
    def _init_database(self):
        """Initialize SQLite database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    sae_id TEXT PRIMARY KEY,
                    user_email TEXT UNIQUE,
                    display_name TEXT,
                    registered_at TEXT,
                    is_active INTEGER DEFAULT 1,
                    last_activity TEXT
                )
            """)
            
            # Key pools metadata table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS key_pools (
                    pool_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sae_id TEXT UNIQUE,
                    total_keys INTEGER DEFAULT 0,
                    used_keys INTEGER DEFAULT 0,
                    available_keys INTEGER DEFAULT 0,
                    last_sync_time TEXT,
                    next_sync_due TEXT,
                    pool_size_limit INTEGER DEFAULT 1000,
                    low_threshold INTEGER DEFAULT 100,
                    FOREIGN KEY (sae_id) REFERENCES users(sae_id)
                )
            """)
            
            # Quantum keys table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS quantum_keys (
                    key_id TEXT PRIMARY KEY,
                    sae_id TEXT,
                    key_data BLOB,
                    key_size INTEGER DEFAULT 1024,
                    status TEXT DEFAULT 'unused',
                    created_at TEXT,
                    used_at TEXT,
                    delivered_to_sae_id TEXT,
                    delivered_at TEXT,
                    FOREIGN KEY (sae_id) REFERENCES users(sae_id)
                )
            """)
            
            # Sync logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sync_logs (
                    sync_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sync_time TEXT,
                    sync_type TEXT,
                    next_door_km_available INTEGER,
                    users_synced INTEGER,
                    total_keys_received INTEGER,
                    errors TEXT,
                    duration_ms INTEGER
                )
            """)
            
            # Key delivery logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS key_delivery_logs (
                    delivery_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key_id TEXT,
                    from_sae_id TEXT,
                    to_sae_id TEXT,
                    delivered_at TEXT,
                    purpose TEXT
                )
            """)
            
            # Create indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_keys_sae_id ON quantum_keys(sae_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_keys_status ON quantum_keys(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_keys_sae_status ON quantum_keys(sae_id, status)")
            
            conn.commit()
            print("[USER_KEY_POOL] Database tables initialized")
    
    def register_user(self, sae_id: str, user_email: str, display_name: str = None,
                      initial_pool_size: int = 1000) -> Dict[str, Any]:
        """
        Register a new user and initialize their key pool.
        
        Args:
            sae_id: Unique SAE ID for the user (e.g., "SAE_001")
            user_email: User's email address
            display_name: Optional display name
            initial_pool_size: Number of keys to generate initially (10-10000)
        
        Returns:
            Registration result with pool details
        """
        with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    # Check if user already exists
                    cursor.execute("SELECT sae_id FROM users WHERE sae_id = ? OR user_email = ?",
                                   (sae_id, user_email))
                    if cursor.fetchone():
                        return {
                            "success": False,
                            "error": "User already registered",
                            "sae_id": sae_id
                        }
                    
                    # Validate pool size
                    initial_pool_size = max(10, min(10000, initial_pool_size))
                    
                    now = datetime.utcnow().isoformat() + "Z"
                    
                    # Insert user
                    cursor.execute("""
                        INSERT INTO users (sae_id, user_email, display_name, registered_at, last_activity)
                        VALUES (?, ?, ?, ?, ?)
                    """, (sae_id, user_email, display_name or user_email.split('@')[0], now, now))
                    
                    # Create key pool
                    cursor.execute("""
                        INSERT INTO key_pools (sae_id, total_keys, used_keys, available_keys,
                                               last_sync_time, pool_size_limit)
                        VALUES (?, 0, 0, 0, ?, ?)
                    """, (sae_id, now, initial_pool_size))
                    
                    conn.commit()
                    
                    # Generate initial keys
                    keys_generated = self._generate_keys_for_user(sae_id, initial_pool_size)
                    
                    print(f"[USER_KEY_POOL] Registered user {sae_id} ({user_email}) with {keys_generated} keys")
                    
                    return {
                        "success": True,
                        "sae_id": sae_id,
                        "user_email": user_email,
                        "pool_size": keys_generated,
                        "keys_generated": keys_generated,
                        "registered_at": now
                    }
                    
            except Exception as e:
                print(f"[USER_KEY_POOL] Error registering user: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "sae_id": sae_id
                }
    
    def _generate_keys_for_user(self, sae_id: str, count: int) -> int:
        """
        Generate quantum keys for a specific user.
        
        Args:
            sae_id: User's SAE ID
            count: Number of keys to generate
        
        Returns:
            Number of keys actually generated
        """
        keys_generated = 0
        now = datetime.utcnow().isoformat() + "Z"
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get current key count for sequence numbering
                cursor.execute("""
                    SELECT COUNT(*) FROM quantum_keys WHERE sae_id = ?
                """, (sae_id,))
                existing_count = cursor.fetchone()[0]
                
                # Generate keys in batches for performance
                batch_size = 100
                for batch_start in range(0, count, batch_size):
                    batch_end = min(batch_start + batch_size, count)
                    batch_keys = []
                    
                    for i in range(batch_start, batch_end):
                        seq_num = existing_count + i + 1
                        key_id = f"qk_{sae_id}_{seq_num:06d}"
                        
                        # Generate 1KB cryptographically secure random key
                        key_data = secrets.token_bytes(KEY_SIZE_BYTES)
                        
                        batch_keys.append((
                            key_id,
                            sae_id,
                            key_data,
                            KEY_SIZE_BYTES,
                            'unused',
                            now,
                            None,  # used_at
                            None,  # delivered_to_sae_id
                            None   # delivered_at
                        ))
                    
                    cursor.executemany("""
                        INSERT INTO quantum_keys 
                        (key_id, sae_id, key_data, key_size, status, created_at, used_at, delivered_to_sae_id, delivered_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, batch_keys)
                    
                    keys_generated += len(batch_keys)
                
                # Update pool metadata
                cursor.execute("""
                    UPDATE key_pools 
                    SET total_keys = total_keys + ?,
                        available_keys = available_keys + ?
                    WHERE sae_id = ?
                """, (keys_generated, keys_generated, sae_id))
                
                conn.commit()
                
        except Exception as e:
            print(f"[USER_KEY_POOL] Error generating keys: {e}")
        
        return keys_generated
    
    def get_keys_for_receiver(self, sender_sae_id: str, receiver_sae_id: str, 
                               number: int, size: int = KEY_SIZE_BYTES) -> Dict[str, Any]:
        """
        Get keys from receiver's pool for sender to use (ETSI GS QKD 014 enc_keys).
        
        CRITICAL: Sender requests keys FROM receiver's pool, NOT sender's own pool!
        This is because in QKD, both parties need the same keys.
        
        Args:
            sender_sae_id: SAE ID of the requesting sender
            receiver_sae_id: SAE ID of the target receiver (keys come from this pool)
            number: Number of keys requested
            size: Key size in bytes (must be 1024)
        
        Returns:
            ETSI GS QKD 014 formatted response with keys
        """
        with self.lock:
            try:
                # Validate key size
                if size != KEY_SIZE_BYTES:
                    return {
                        "error": f"Invalid key size. Must be {KEY_SIZE_BYTES} bytes (1KB)",
                        "requested_size": size,
                        "required_size": KEY_SIZE_BYTES
                    }
                
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    # Check if receiver exists
                    cursor.execute("SELECT sae_id FROM users WHERE sae_id = ?", (receiver_sae_id,))
                    if not cursor.fetchone():
                        return {
                            "error": "Receiver not found",
                            "receiver_sae_id": receiver_sae_id,
                            "status_code": 404
                        }
                    
                    # Get available keys from receiver's pool
                    cursor.execute("""
                        SELECT available_keys FROM key_pools WHERE sae_id = ?
                    """, (receiver_sae_id,))
                    pool_info = cursor.fetchone()
                    
                    if not pool_info:
                        return {
                            "error": "Receiver has no key pool",
                            "receiver_sae_id": receiver_sae_id,
                            "status_code": 404
                        }
                    
                    available = pool_info[0]
                    
                    if available < number:
                        return {
                            "error": "Insufficient keys available",
                            "available_keys": available,
                            "requested_keys": number,
                            "status_code": 400
                        }
                    
                    # Retrieve unused keys from receiver's pool
                    cursor.execute("""
                        SELECT key_id, key_data FROM quantum_keys 
                        WHERE sae_id = ? AND status = 'unused'
                        ORDER BY created_at ASC
                        LIMIT ?
                    """, (receiver_sae_id, number))
                    
                    rows = cursor.fetchall()
                    
                    if len(rows) < number:
                        return {
                            "error": "Insufficient unused keys",
                            "available_keys": len(rows),
                            "requested_keys": number,
                            "status_code": 400
                        }
                    
                    now = datetime.utcnow().isoformat() + "Z"
                    keys = []
                    key_ids = []
                    
                    for key_id, key_data in rows:
                        # Base64 encode the key data for JSON transport
                        key_b64 = base64.b64encode(key_data).decode('utf-8')
                        keys.append({
                            "key_ID": key_id,
                            "key": key_b64
                        })
                        key_ids.append(key_id)
                    
                    # Mark keys as used and record delivery
                    cursor.executemany("""
                        UPDATE quantum_keys 
                        SET status = 'used', used_at = ?, delivered_to_sae_id = ?, delivered_at = ?
                        WHERE key_id = ?
                    """, [(now, sender_sae_id, now, kid) for kid in key_ids])
                    
                    # Update pool counts
                    cursor.execute("""
                        UPDATE key_pools 
                        SET used_keys = used_keys + ?,
                            available_keys = available_keys - ?
                        WHERE sae_id = ?
                    """, (len(keys), len(keys), receiver_sae_id))
                    
                    # Log deliveries
                    cursor.executemany("""
                        INSERT INTO key_delivery_logs (key_id, from_sae_id, to_sae_id, delivered_at, purpose)
                        VALUES (?, ?, ?, ?, 'encryption')
                    """, [(kid, receiver_sae_id, sender_sae_id, now) for kid in key_ids])
                    
                    conn.commit()
                    
                    print(f"[USER_KEY_POOL] Delivered {len(keys)} keys from {receiver_sae_id}'s pool to {sender_sae_id}")
                    
                    return {
                        "keys": keys,
                        "source_pool": receiver_sae_id,
                        "delivered_to": sender_sae_id,
                        "count": len(keys)
                    }
                    
            except Exception as e:
                print(f"[USER_KEY_POOL] Error getting keys: {e}")
                return {
                    "error": str(e),
                    "status_code": 500
                }
    
    def get_keys_by_ids(self, sae_id: str, key_ids: List[str]) -> Dict[str, Any]:
        """
        Retrieve specific keys by their IDs (for decryption - dec_keys endpoint).
        
        Args:
            sae_id: SAE ID of the requesting user
            key_ids: List of key IDs to retrieve
        
        Returns:
            ETSI GS QKD 014 formatted response with keys
        """
        with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    keys = []
                    found_ids = []
                    
                    for key_id in key_ids:
                        cursor.execute("""
                            SELECT key_id, key_data, sae_id, status, delivered_to_sae_id
                            FROM quantum_keys WHERE key_id = ?
                        """, (key_id,))
                        
                        row = cursor.fetchone()
                        
                        if row:
                            key_id, key_data, owner_sae_id, status, delivered_to = row
                            
                            # Security check: Only allow retrieval if:
                            # 1. User owns the key (owner_sae_id == sae_id)
                            # 2. Key was delivered to user (delivered_to_sae_id == sae_id)
                            if owner_sae_id == sae_id or delivered_to == sae_id:
                                key_b64 = base64.b64encode(key_data).decode('utf-8')
                                keys.append({
                                    "key_ID": key_id,
                                    "key": key_b64
                                })
                                found_ids.append(key_id)
                            else:
                                print(f"[USER_KEY_POOL] Access denied: {sae_id} tried to access key {key_id} (owner: {owner_sae_id})")
                    
                    missing_ids = [kid for kid in key_ids if kid not in found_ids]
                    
                    result = {"keys": keys}
                    
                    if missing_ids:
                        result["missing_keys"] = missing_ids
                        result["warning"] = f"{len(missing_ids)} keys not found or access denied"
                    
                    print(f"[USER_KEY_POOL] Retrieved {len(keys)}/{len(key_ids)} keys for {sae_id}")
                    
                    return result
                    
            except Exception as e:
                print(f"[USER_KEY_POOL] Error retrieving keys by ID: {e}")
                return {
                    "error": str(e),
                    "keys": []
                }
    
    def get_pool_status(self, sae_id: str) -> Dict[str, Any]:
        """
        Get the status of a user's key pool.
        
        Args:
            sae_id: User's SAE ID
        
        Returns:
            Pool status including total, used, and available keys
        """
        with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        SELECT u.user_email, p.total_keys, p.used_keys, p.available_keys,
                               p.last_sync_time, p.next_sync_due, p.pool_size_limit, p.low_threshold
                        FROM users u
                        JOIN key_pools p ON u.sae_id = p.sae_id
                        WHERE u.sae_id = ?
                    """, (sae_id,))
                    
                    row = cursor.fetchone()
                    
                    if not row:
                        return {
                            "error": "User not found",
                            "sae_id": sae_id,
                            "status_code": 404
                        }
                    
                    email, total, used, available, last_sync, next_sync, limit, threshold = row
                    
                    # Check if pool is low
                    is_low = available < threshold
                    usage_percent = (used / total * 100) if total > 0 else 0
                    
                    return {
                        "sae_id": sae_id,
                        "user_email": email,
                        "total_keys": total,
                        "used_keys": used,
                        "available_keys": available,
                        "usage_percent": round(usage_percent, 2),
                        "pool_size_limit": limit,
                        "low_threshold": threshold,
                        "is_low": is_low,
                        "last_sync": last_sync,
                        "next_sync": next_sync,
                        "key_size_bytes": KEY_SIZE_BYTES,
                        "key_size_bits": KEY_SIZE_BITS
                    }
                    
            except Exception as e:
                print(f"[USER_KEY_POOL] Error getting pool status: {e}")
                return {
                    "error": str(e),
                    "sae_id": sae_id
                }
    
    def get_all_pools_status(self) -> Dict[str, Any]:
        """Get status of all user key pools."""
        with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        SELECT u.sae_id, u.user_email, p.total_keys, p.used_keys, p.available_keys,
                               p.low_threshold
                        FROM users u
                        JOIN key_pools p ON u.sae_id = p.sae_id
                        WHERE u.is_active = 1
                        ORDER BY u.sae_id
                    """)
                    
                    pools = []
                    total_keys = 0
                    total_available = 0
                    low_pools = 0
                    
                    for row in cursor.fetchall():
                        sae_id, email, total, used, available, threshold = row
                        is_low = available < threshold
                        if is_low:
                            low_pools += 1
                        
                        pools.append({
                            "sae_id": sae_id,
                            "user_email": email,
                            "total_keys": total,
                            "used_keys": used,
                            "available_keys": available,
                            "is_low": is_low
                        })
                        
                        total_keys += total
                        total_available += available
                    
                    return {
                        "pools": pools,
                        "summary": {
                            "total_users": len(pools),
                            "total_keys": total_keys,
                            "total_available": total_available,
                            "low_pool_count": low_pools
                        }
                    }
                    
            except Exception as e:
                print(f"[USER_KEY_POOL] Error getting all pools: {e}")
                return {"error": str(e), "pools": []}
    
    def refill_pool(self, sae_id: str, keys_to_add: int = None) -> Dict[str, Any]:
        """
        Refill a user's key pool with new keys.
        
        Args:
            sae_id: User's SAE ID
            keys_to_add: Number of keys to add (default: fill to limit)
        
        Returns:
            Refill result
        """
        with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        SELECT available_keys, pool_size_limit FROM key_pools WHERE sae_id = ?
                    """, (sae_id,))
                    
                    row = cursor.fetchone()
                    if not row:
                        return {"error": "User not found", "sae_id": sae_id}
                    
                    available, limit = row
                    
                    # Calculate how many keys to add
                    if keys_to_add is None:
                        keys_to_add = limit - available
                    else:
                        keys_to_add = min(keys_to_add, limit - available)
                    
                    if keys_to_add <= 0:
                        return {
                            "success": True,
                            "sae_id": sae_id,
                            "keys_added": 0,
                            "message": "Pool is already at capacity"
                        }
                    
                    # Generate new keys
                    keys_generated = self._generate_keys_for_user(sae_id, keys_to_add)
                    
                    print(f"[USER_KEY_POOL] Refilled {sae_id} with {keys_generated} keys")
                    
                    return {
                        "success": True,
                        "sae_id": sae_id,
                        "keys_added": keys_generated,
                        "available_before": available,
                        "available_after": available + keys_generated
                    }
                    
            except Exception as e:
                print(f"[USER_KEY_POOL] Error refilling pool: {e}")
                return {"error": str(e), "sae_id": sae_id}
    
    def get_low_pools(self) -> List[Dict[str, Any]]:
        """Get list of pools that are below their low threshold."""
        with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        SELECT u.sae_id, u.user_email, p.available_keys, p.low_threshold,
                               p.pool_size_limit
                        FROM users u
                        JOIN key_pools p ON u.sae_id = p.sae_id
                        WHERE p.available_keys < p.low_threshold AND u.is_active = 1
                    """)
                    
                    low_pools = []
                    for row in cursor.fetchall():
                        sae_id, email, available, threshold, limit = row
                        low_pools.append({
                            "sae_id": sae_id,
                            "user_email": email,
                            "available_keys": available,
                            "low_threshold": threshold,
                            "pool_size_limit": limit,
                            "keys_needed": limit - available
                        })
                    
                    return low_pools
                    
            except Exception as e:
                print(f"[USER_KEY_POOL] Error getting low pools: {e}")
                return []
    
    def delete_user(self, sae_id: str) -> Dict[str, Any]:
        """
        Delete a user and all their keys.
        
        Args:
            sae_id: User's SAE ID to delete
        
        Returns:
            Deletion result
        """
        with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    # Get counts before deletion
                    cursor.execute("SELECT COUNT(*) FROM quantum_keys WHERE sae_id = ?", (sae_id,))
                    keys_deleted = cursor.fetchone()[0]
                    
                    # Delete keys
                    cursor.execute("DELETE FROM quantum_keys WHERE sae_id = ?", (sae_id,))
                    
                    # Delete pool
                    cursor.execute("DELETE FROM key_pools WHERE sae_id = ?", (sae_id,))
                    
                    # Delete delivery logs
                    cursor.execute("""
                        DELETE FROM key_delivery_logs WHERE from_sae_id = ? OR to_sae_id = ?
                    """, (sae_id, sae_id))
                    
                    # Delete user
                    cursor.execute("DELETE FROM users WHERE sae_id = ?", (sae_id,))
                    
                    conn.commit()
                    
                    print(f"[USER_KEY_POOL] Deleted user {sae_id} and {keys_deleted} keys")
                    
                    return {
                        "success": True,
                        "sae_id": sae_id,
                        "keys_deleted": keys_deleted
                    }
                    
            except Exception as e:
                print(f"[USER_KEY_POOL] Error deleting user: {e}")
                return {"error": str(e), "sae_id": sae_id}


# Global instance
_user_key_pool: Optional[UserKeyPool] = None
_pool_lock = threading.Lock()


def get_user_key_pool(db_path: str = None) -> UserKeyPool:
    """Get or create the global UserKeyPool instance."""
    global _user_key_pool
    
    with _pool_lock:
        if _user_key_pool is None:
            if db_path is None:
                db_path = os.getenv('USER_KEY_POOL_DB', 'user_key_pools.db')
            _user_key_pool = UserKeyPool(db_path)
    
    return _user_key_pool
