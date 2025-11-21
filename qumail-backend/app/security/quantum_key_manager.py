"""
One-Time Quantum Key Management System for QuMail
Implements secure one-time-use quantum keys with consumption tracking
Ensures keys are never reused and provides perfect forward secrecy
"""

import asyncio
import json
import uuid
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Any
from pathlib import Path
import logging
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import sqlite3
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecurityLevel(Enum):
    """Security levels for quantum encryption"""
    LOW = "low"           # 32-byte quantum keys, basic encryption
    MEDIUM = "medium"     # 64-byte quantum keys, enhanced encryption  
    HIGH = "high"         # 128-byte quantum keys, military-grade encryption
    ULTRA = "ultra"       # 256-byte quantum keys, maximum security

@dataclass
class QuantumKeyRecord:
    """Record of a quantum key with consumption tracking"""
    key_id: str
    key_data: str  # Base64 encoded quantum key
    security_level: SecurityLevel
    kme_source: str  # KME-1 or KME-2
    created_at: datetime
    consumed_at: Optional[datetime] = None
    consumed_by: Optional[str] = None  # User/operation that consumed the key
    message_id: Optional[str] = None   # Associated message ID
    is_consumed: bool = False

class QuantumKeyDatabase:
    """Secure database for tracking quantum key usage"""
    
    def __init__(self, db_path: str = "quantum_keys.db"):
        self.db_path = db_path
        self.lock = threading.Lock()
        self._init_database()
    
    def _init_database(self):
        """Initialize the quantum key tracking database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS quantum_keys (
                    key_id TEXT PRIMARY KEY,
                    key_data_hash TEXT NOT NULL,  -- Hash of key data for verification
                    security_level TEXT NOT NULL,
                    kme_source TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    consumed_at TEXT,
                    consumed_by TEXT,
                    message_id TEXT,
                    is_consumed BOOLEAN DEFAULT FALSE
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS key_consumption_audit (
                    audit_id TEXT PRIMARY KEY,
                    key_id TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    user_id TEXT,
                    timestamp TEXT NOT NULL,
                    details TEXT,
                    FOREIGN KEY (key_id) REFERENCES quantum_keys (key_id)
                )
            """)
            
            conn.execute("CREATE INDEX IF NOT EXISTS idx_consumed ON quantum_keys (is_consumed)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_security_level ON quantum_keys (security_level)")
            conn.commit()
    
    def store_key(self, key_record: QuantumKeyRecord) -> bool:
        """Store a quantum key record with consumption tracking"""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    # Hash the key data for secure storage
                    key_hash = hashlib.sha256(key_record.key_data.encode()).hexdigest()
                    
                    conn.execute("""
                        INSERT INTO quantum_keys 
                        (key_id, key_data_hash, security_level, kme_source, created_at, is_consumed)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        key_record.key_id,
                        key_hash,
                        key_record.security_level.value,
                        key_record.kme_source,
                        key_record.created_at.isoformat(),
                        key_record.is_consumed
                    ))
                    
                    # Audit log
                    self._audit_operation(conn, key_record.key_id, "KEY_STORED", None, "Key stored in quantum database")
                    conn.commit()
                    
            logger.info(f"Stored quantum key {key_record.key_id} for security level {key_record.security_level.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store quantum key: {e}")
            return False
    
    def consume_key(self, key_id: str, consumer: str, message_id: str) -> bool:
        """Mark a quantum key as consumed (one-time use)"""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    # Check if key exists and is not consumed
                    cursor = conn.execute(
                        "SELECT is_consumed FROM quantum_keys WHERE key_id = ?", 
                        (key_id,)
                    )
                    result = cursor.fetchone()
                    
                    if not result:
                        logger.error(f"Quantum key {key_id} not found")
                        return False
                    
                    if result[0]:  # Already consumed
                        logger.error(f"Quantum key {key_id} already consumed - cannot reuse")
                        return False
                    
                    # Mark key as consumed
                    conn.execute("""
                        UPDATE quantum_keys 
                        SET consumed_at = ?, consumed_by = ?, message_id = ?, is_consumed = TRUE
                        WHERE key_id = ?
                    """, (
                        datetime.now().isoformat(),
                        consumer,
                        message_id,
                        key_id
                    ))
                    
                    # Audit log
                    self._audit_operation(
                        conn, key_id, "KEY_CONSUMED", consumer, 
                        f"Key consumed for message {message_id}"
                    )
                    conn.commit()
                    
            logger.info(f"Consumed quantum key {key_id} for message {message_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to consume quantum key: {e}")
            return False
    
    def is_key_consumed(self, key_id: str) -> bool:
        """Check if a quantum key has been consumed"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT is_consumed FROM quantum_keys WHERE key_id = ?", 
                    (key_id,)
                )
                result = cursor.fetchone()
                return bool(result and result[0]) if result else False
        except Exception as e:
            logger.error(f"Error checking key consumption: {e}")
            return True  # Fail safe - assume consumed
    
    def _audit_operation(self, conn, key_id: str, operation: str, user_id: str, details: str):
        """Add audit log entry"""
        audit_id = str(uuid.uuid4())
        conn.execute("""
            INSERT INTO key_consumption_audit 
            (audit_id, key_id, operation, user_id, timestamp, details)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (audit_id, key_id, operation, user_id, datetime.now().isoformat(), details))
    
    def get_consumption_stats(self) -> Dict[str, int]:
        """Get quantum key consumption statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT 
                        security_level,
                        COUNT(*) as total_keys,
                        SUM(CASE WHEN is_consumed THEN 1 ELSE 0 END) as consumed_keys
                    FROM quantum_keys 
                    GROUP BY security_level
                """)
                
                stats = {}
                for row in cursor.fetchall():
                    level, total, consumed = row
                    stats[level] = {
                        "total_keys": total,
                        "consumed_keys": consumed,
                        "available_keys": total - consumed
                    }
                
                return stats
        except Exception as e:
            logger.error(f"Error getting consumption stats: {e}")
            return {}

class OneTimeQuantumKeyManager:
    """Manages one-time-use quantum keys across all security levels"""
    
    def __init__(self, km_clients):
        """Initialize with KM clients from the existing system"""
        self.km1_client = km_clients[0]  # KME-1 client
        self.km2_client = km_clients[1]  # KME-2 client
        self.db = QuantumKeyDatabase()
        
        # Security level to key size mapping (bytes)
        self.security_key_sizes = {
            SecurityLevel.LOW: 32,      # 256-bit
            SecurityLevel.MEDIUM: 64,   # 512-bit
            SecurityLevel.HIGH: 128,    # 1024-bit
            SecurityLevel.ULTRA: 256    # 2048-bit
        }
        
        # Minimum key pool sizes per security level
        self.min_key_pools = {
            SecurityLevel.LOW: 10,
            SecurityLevel.MEDIUM: 8,
            SecurityLevel.HIGH: 6,
            SecurityLevel.ULTRA: 4
        }
        
        logger.info("Initialized One-Time Quantum Key Manager with SSL/TLS security")
    
    async def get_quantum_key_for_security_level(self, security_level: SecurityLevel, 
                                               user_id: str, message_id: str) -> Optional[str]:
        """Get a one-time quantum key for specified security level"""
        try:
            # Determine key size for security level
            key_size = self.security_key_sizes[security_level]
            
            # Try to get key from KME-1 first, then KME-2
            quantum_key = None
            kme_source = None
            
            try:
                # Request quantum key from KME-1
                keys = await self.km1_client.request_keys(1, key_size)
                if keys:
                    quantum_key = keys[0]["key"]
                    kme_source = "KME-1"
            except Exception as e:
                logger.warning(f"KME-1 failed, trying KME-2: {e}")
            
            if not quantum_key:
                try:
                    # Fallback to KME-2
                    keys = await self.km2_client.request_keys(1, key_size)
                    if keys:
                        quantum_key = keys[0]["key"]
                        kme_source = "KME-2"
                except Exception as e:
                    logger.error(f"Both KME servers failed: {e}")
                    return None
            
            if not quantum_key:
                logger.error(f"No quantum keys available for security level {security_level.value}")
                return None
            
            # Create key record
            key_id = str(uuid.uuid4())
            key_record = QuantumKeyRecord(
                key_id=key_id,
                key_data=quantum_key,
                security_level=security_level,
                kme_source=kme_source,
                created_at=datetime.now()
            )
            
            # Store key in database
            if self.db.store_key(key_record):
                # Immediately consume the key for this message
                if self.db.consume_key(key_id, user_id, message_id):
                    logger.info(f"Generated and consumed one-time quantum key {key_id} for {security_level.value} security")
                    return quantum_key
                else:
                    logger.error(f"Failed to consume quantum key {key_id}")
                    return None
            else:
                logger.error(f"Failed to store quantum key {key_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting quantum key for security level {security_level.value}: {e}")
            return None
    
    async def verify_key_consumption(self, key_id: str) -> bool:
        """Verify that a quantum key has been properly consumed"""
        return self.db.is_key_consumed(key_id)
    
    def get_security_level_stats(self) -> Dict[str, Any]:
        """Get statistics for all security levels"""
        stats = self.db.get_consumption_stats()
        
        # Add security level details
        for level in SecurityLevel:
            if level.value not in stats:
                stats[level.value] = {
                    "total_keys": 0,
                    "consumed_keys": 0,
                    "available_keys": 0
                }
            
            stats[level.value]["key_size_bytes"] = self.security_key_sizes[level]
            stats[level.value]["min_pool_size"] = self.min_key_pools[level]
        
        return stats
    
    async def preload_quantum_keys(self, security_level: SecurityLevel, count: int = 5):
        """Preload quantum keys for faster access (still one-time use)"""
        try:
            key_size = self.security_key_sizes[security_level]
            
            # Request keys from both KME servers
            kme1_keys = await self.km1_client.request_keys(count // 2, key_size)
            kme2_keys = await self.km2_client.request_keys(count - count // 2, key_size)
            
            stored_count = 0
            
            # Store KME-1 keys
            if kme1_keys:
                for key_data in kme1_keys:
                    key_record = QuantumKeyRecord(
                        key_id=str(uuid.uuid4()),
                        key_data=key_data["key"],
                        security_level=security_level,
                        kme_source="KME-1",
                        created_at=datetime.now()
                    )
                    if self.db.store_key(key_record):
                        stored_count += 1
            
            # Store KME-2 keys
            if kme2_keys:
                for key_data in kme2_keys:
                    key_record = QuantumKeyRecord(
                        key_id=str(uuid.uuid4()),
                        key_data=key_data["key"],
                        security_level=security_level,
                        kme_source="KME-2",
                        created_at=datetime.now()
                    )
                    if self.db.store_key(key_record):
                        stored_count += 1
            
            logger.info(f"Preloaded {stored_count} quantum keys for {security_level.value} security level")
            return stored_count
            
        except Exception as e:
            logger.error(f"Error preloading quantum keys: {e}")
            return 0

# Global instance
quantum_key_manager = None

async def initialize_quantum_key_manager(km_clients):
    """Initialize the global quantum key manager"""
    global quantum_key_manager
    quantum_key_manager = OneTimeQuantumKeyManager(km_clients)
    
    # Preload keys for all security levels
    for level in SecurityLevel:
        await quantum_key_manager.preload_quantum_keys(level, 3)
    
    logger.info("Quantum Key Manager initialized with one-time-use security")
    return quantum_key_manager

def get_quantum_key_manager() -> OneTimeQuantumKeyManager:
    """Get the global quantum key manager instance"""
    if quantum_key_manager is None:
        raise RuntimeError("Quantum Key Manager not initialized")
    return quantum_key_manager