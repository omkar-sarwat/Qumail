"""
QKD MongoDB Service
Integrates KME key retrieval with MongoDB storage for complete QKD lifecycle tracking.
All quantum keys are stored in MongoDB for audit, tracking, and retrieval.
"""

import logging
import base64
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

from ..mongo_models import (
    QKDKeyDocument,
    QKDKeyState,
    QKDSessionDocument,
    QKDAuditLogDocument,
    QKDKeyPoolStatusDocument
)
from ..mongo_repositories import (
    QKDKeyRepository,
    QKDSessionRepository,
    QKDAuditLogRepository,
    QKDKeyPoolStatusRepository
)
from .kme_service import KmeService, KmeServiceError

logger = logging.getLogger(__name__)


class QKDMongoService:
    """
    QKD Service with MongoDB integration.
    All quantum keys retrieved from KME servers are stored in MongoDB
    for complete lifecycle tracking, audit logging, and retrieval.
    """
    
    # Default key expiration time
    KEY_EXPIRATION_HOURS = 24
    
    def __init__(self):
        """Initialize the QKD MongoDB service."""
        self.kme_service = KmeService()
        logger.info("QKD MongoDB Service initialized")
    
    async def get_encryption_keys(
        self,
        db: Any,
        security_level: int,
        sender_email: str,
        receiver_email: str,
        count: int = 1,
        key_size_bits: int = 256,
        flow_id: str = None
    ) -> List[Dict[str, Any]]:
        """
        Get encryption keys from KME and store them in MongoDB.
        
        Args:
            db: MongoDB database connection
            security_level: Encryption security level (1-4)
            sender_email: Sender's email address
            receiver_email: Receiver's email address
            count: Number of keys to retrieve
            key_size_bits: Size of keys in bits
            flow_id: Optional flow ID for tracking
            
        Returns:
            List of key data dictionaries with key_id and key material
        """
        key_repo = QKDKeyRepository(db)
        audit_repo = QKDAuditLogRepository(db)
        pool_repo = QKDKeyPoolStatusRepository(db)
        
        try:
            # Get keys from KME1 (sender's KME)
            server_id = 1
            slave_sae_id = self.kme_service.kme_servers[0]["slave_sae_id"]
            
            logger.info(f"[QKD MongoDB] Requesting {count} keys from KME1 for {sender_email} -> {receiver_email}")
            
            # Retrieve keys from KME
            kme_keys = await self.kme_service.get_encryption_keys(
                server_id=server_id,
                slave_sae_id=slave_sae_id,
                count=count,
                sender_email=sender_email,
                receiver_email=receiver_email
            )
            
            stored_keys = []
            
            for kme_key in kme_keys:
                key_id = kme_key.get("key_ID") or kme_key.get("key_id")
                key_material = kme_key.get("key")
                key_size = kme_key.get("key_size_bits", key_size_bits)
                
                # Hash the key material for integrity verification
                if key_material:
                    key_hash = hashlib.sha256(base64.b64decode(key_material)).hexdigest()
                else:
                    key_hash = None
                
                # Create QKD key document
                qkd_key = QKDKeyDocument(
                    key_id=key_id,
                    kme1_key_id=key_id,
                    key_material_encrypted=key_material,  # Store base64 encoded
                    key_hash=key_hash,
                    key_size_bits=key_size,
                    source_kme="KME1",
                    sae1_id=slave_sae_id,
                    sender_email=sender_email,
                    receiver_email=receiver_email,
                    flow_id=flow_id,
                    security_level=security_level,
                    algorithm=self._get_algorithm_for_level(security_level),
                    state=QKDKeyState.READY,
                    expires_at=datetime.utcnow() + timedelta(hours=self.KEY_EXPIRATION_HOURS),
                    entropy_score=1.0,
                    quality_score=1.0,
                    quantum_grade=True,
                    operation_history=[{
                        "operation": "GENERATED",
                        "timestamp": datetime.utcnow().isoformat(),
                        "source": "KME1"
                    }]
                )
                
                # Store in MongoDB
                await key_repo.create(qkd_key)
                
                # Log the operation
                await audit_repo.log_operation(
                    operation="KEY_GENERATED",
                    key_id=key_id,
                    flow_id=flow_id,
                    user_email=sender_email,
                    success=True,
                    details={
                        "security_level": security_level,
                        "receiver_email": receiver_email,
                        "key_size_bits": key_size,
                        "source_kme": "KME1"
                    }
                )
                
                stored_keys.append({
                    "key_id": key_id,
                    "key": key_material,
                    "key_size_bits": key_size,
                    "stored_in_mongodb": True
                })
                
                logger.info(f"[QKD MongoDB] Key {key_id[:16]}... stored in MongoDB")
            
            # Update pool status
            await pool_repo.record_key_generated("KME1")
            
            return stored_keys
            
        except KmeServiceError as e:
            logger.error(f"[QKD MongoDB] KME error: {e}")
            await audit_repo.log_operation(
                operation="KEY_GENERATION_FAILED",
                flow_id=flow_id,
                user_email=sender_email,
                success=False,
                error_message=str(e),
                severity="ERROR"
            )
            raise
        except Exception as e:
            logger.error(f"[QKD MongoDB] Error storing keys: {e}")
            raise
    
    async def get_decryption_key(
        self,
        db: Any,
        key_id: str,
        receiver_email: str,
        flow_id: str = None
    ) -> Dict[str, Any]:
        """
        Get decryption key, first checking MongoDB then falling back to KME.
        
        Args:
            db: MongoDB database connection
            key_id: Key ID to retrieve
            receiver_email: Receiver's email for verification
            flow_id: Optional flow ID for tracking
            
        Returns:
            Key data dictionary
        """
        key_repo = QKDKeyRepository(db)
        audit_repo = QKDAuditLogRepository(db)
        
        try:
            # First, try to find the key in MongoDB
            existing_key = await key_repo.find_by_key_id(key_id)
            
            if existing_key and existing_key.key_material_encrypted:
                logger.info(f"[QKD MongoDB] Found key {key_id[:16]}... in MongoDB")
                
                # Verify receiver
                if existing_key.receiver_email and existing_key.receiver_email != receiver_email:
                    logger.warning(f"[QKD MongoDB] Receiver mismatch: {receiver_email} vs stored {existing_key.receiver_email}")
                
                # Log access
                await audit_repo.log_operation(
                    operation="KEY_ACCESSED",
                    key_id=key_id,
                    flow_id=flow_id,
                    user_email=receiver_email,
                    success=True,
                    details={"source": "mongodb_cache"}
                )
                
                return {
                    "key_id": existing_key.key_id,
                    "key": existing_key.key_material_encrypted,
                    "key_size_bits": existing_key.key_size_bits,
                    "from_cache": True
                }
            
            # If not in MongoDB, retrieve from KME2
            server_id = 2
            master_sae_id = self.kme_service.kme_servers[1]["slave_sae_id"]
            
            logger.info(f"[QKD MongoDB] Retrieving key {key_id[:16]}... from KME2")
            
            kme_key = await self.kme_service.get_decryption_key(
                server_id=server_id,
                master_sae_id=master_sae_id,
                key_id=key_id,
                receiver_email=receiver_email
            )
            
            key_material = kme_key.get("key")
            key_size = kme_key.get("key_size_bits", 256)
            
            # Store/update in MongoDB
            if existing_key:
                # Update existing key with KME2 info
                await key_repo.collection.update_one(
                    {"key_id": key_id},
                    {
                        "$set": {
                            "kme2_key_id": key_id,
                            "last_accessed_at": datetime.utcnow()
                        }
                    }
                )
            else:
                # Create new key document
                key_hash = hashlib.sha256(base64.b64decode(key_material)).hexdigest() if key_material else None
                
                qkd_key = QKDKeyDocument(
                    key_id=key_id,
                    kme2_key_id=key_id,
                    key_material_encrypted=key_material,
                    key_hash=key_hash,
                    key_size_bits=key_size,
                    source_kme="KME2",
                    receiver_email=receiver_email,
                    flow_id=flow_id,
                    state=QKDKeyState.READY,
                    expires_at=datetime.utcnow() + timedelta(hours=self.KEY_EXPIRATION_HOURS)
                )
                await key_repo.create(qkd_key)
            
            # Log the operation
            await audit_repo.log_operation(
                operation="KEY_RETRIEVED",
                key_id=key_id,
                flow_id=flow_id,
                user_email=receiver_email,
                success=True,
                details={
                    "source_kme": "KME2",
                    "key_size_bits": key_size
                }
            )
            
            return {
                "key_id": key_id,
                "key": key_material,
                "key_size_bits": key_size,
                "from_cache": False
            }
            
        except KmeServiceError as e:
            logger.error(f"[QKD MongoDB] KME error getting decryption key: {e}")
            await audit_repo.log_operation(
                operation="KEY_RETRIEVAL_FAILED",
                key_id=key_id,
                flow_id=flow_id,
                user_email=receiver_email,
                success=False,
                error_message=str(e),
                severity="ERROR"
            )
            raise
        except Exception as e:
            logger.error(f"[QKD MongoDB] Error: {e}")
            raise
    
    async def consume_key(
        self,
        db: Any,
        key_id: str,
        user_id: str,
        email_id: str = None
    ) -> bool:
        """
        Mark a key as consumed (one-time use).
        
        Args:
            db: MongoDB database connection
            key_id: Key ID to consume
            user_id: User ID consuming the key
            email_id: Associated email ID
            
        Returns:
            True if key was consumed successfully
        """
        key_repo = QKDKeyRepository(db)
        audit_repo = QKDAuditLogRepository(db)
        pool_repo = QKDKeyPoolStatusRepository(db)
        
        success = await key_repo.consume_key(key_id, user_id, email_id)
        
        if success:
            await audit_repo.log_operation(
                operation="KEY_CONSUMED",
                key_id=key_id,
                user_id=user_id,
                success=True,
                details={"email_id": email_id}
            )
            await pool_repo.record_key_consumed("KME1")
            logger.info(f"[QKD MongoDB] Key {key_id[:16]}... consumed by user {user_id}")
        else:
            await audit_repo.log_operation(
                operation="KEY_CONSUMPTION_FAILED",
                key_id=key_id,
                user_id=user_id,
                success=False,
                error_message="Key not found or already consumed",
                severity="WARNING"
            )
            logger.warning(f"[QKD MongoDB] Failed to consume key {key_id[:16]}...")
        
        return success
    
    async def create_session(
        self,
        db: Any,
        sender_email: str,
        receiver_email: str,
        security_level: int,
        flow_id: str = None
    ) -> QKDSessionDocument:
        """
        Create a new QKD session for key exchange.
        
        Args:
            db: MongoDB database connection
            sender_email: Sender's email
            receiver_email: Receiver's email
            security_level: Security level (1-4)
            flow_id: Optional flow ID
            
        Returns:
            Created session document
        """
        session_repo = QKDSessionRepository(db)
        audit_repo = QKDAuditLogRepository(db)
        
        session = QKDSessionDocument(
            flow_id=flow_id,
            sender_email=sender_email,
            sender_sae_id=self.kme_service.kme_servers[0]["slave_sae_id"],
            receiver_email=receiver_email,
            receiver_sae_id=self.kme_service.kme_servers[1]["slave_sae_id"],
            kme1_endpoint=self.kme_service.kme_servers[0]["base_url"],
            kme2_endpoint=self.kme_service.kme_servers[1]["base_url"],
            security_level=security_level,
            encryption_algorithm=self._get_algorithm_for_level(security_level),
            expires_at=datetime.utcnow() + timedelta(hours=self.KEY_EXPIRATION_HOURS)
        )
        
        await session_repo.create(session)
        
        await audit_repo.log_operation(
            operation="SESSION_CREATED",
            session_id=session.session_id,
            flow_id=flow_id,
            user_email=sender_email,
            success=True,
            details={
                "receiver_email": receiver_email,
                "security_level": security_level
            }
        )
        
        logger.info(f"[QKD MongoDB] Session created: {session.session_id}")
        return session
    
    async def complete_session(
        self,
        db: Any,
        session_id: str,
        success: bool = True,
        error_message: str = None
    ) -> bool:
        """Complete a QKD session."""
        session_repo = QKDSessionRepository(db)
        audit_repo = QKDAuditLogRepository(db)
        
        result = await session_repo.complete_session(session_id, success, error_message)
        
        await audit_repo.log_operation(
            operation="SESSION_COMPLETED",
            session_id=session_id,
            success=success,
            error_message=error_message,
            severity="INFO" if success else "WARNING"
        )
        
        return result
    
    async def get_statistics(self, db: Any) -> Dict[str, Any]:
        """Get QKD key pool statistics from MongoDB."""
        key_repo = QKDKeyRepository(db)
        session_repo = QKDSessionRepository(db)
        
        key_stats = await key_repo.get_statistics()
        session_stats = await session_repo.get_session_statistics()
        
        return {
            "keys": key_stats,
            "sessions": session_stats,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def get_audit_logs(
        self,
        db: Any,
        hours: int = 24,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get recent QKD audit logs."""
        audit_repo = QKDAuditLogRepository(db)
        logs = await audit_repo.find_recent(hours=hours, limit=limit)
        return [log.dict() for log in logs]
    
    async def cleanup_expired_keys(self, db: Any) -> int:
        """Clean up expired keys in MongoDB."""
        key_repo = QKDKeyRepository(db)
        audit_repo = QKDAuditLogRepository(db)
        
        count = await key_repo.cleanup_expired_keys()
        
        if count > 0:
            await audit_repo.log_operation(
                operation="KEYS_EXPIRED_CLEANUP",
                success=True,
                details={"expired_count": count}
            )
            logger.info(f"[QKD MongoDB] Cleaned up {count} expired keys")
        
        return count
    
    def _get_algorithm_for_level(self, security_level: int) -> str:
        """Get the encryption algorithm name for a security level."""
        algorithms = {
            1: "OTP (One-Time Pad)",
            2: "AES-256-GCM",
            3: "ML-KEM-1024 + ML-DSA-87 (PQC)",
            4: "RSA-4096 + AES-256-GCM"
        }
        return algorithms.get(security_level, f"Level-{security_level}")


# Global instance
qkd_mongo_service = QKDMongoService()
