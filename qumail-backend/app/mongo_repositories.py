"""Repository pattern for MongoDB data access."""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
from .mongo_models import (
    UserDocument,
    EmailDocument,
    DraftDocument,
    EncryptionMetadataDocument,
    KeyUsageDocument,
    AttachmentDocument,
    EmailDirection,
    # QKD Models
    QKDKeyDocument,
    QKDKeyState,
    QKDSessionDocument,
    QKDAuditLogDocument,
    QKDKeyPoolStatusDocument
)
import logging

logger = logging.getLogger(__name__)

class UserRepository:
    """Repository for user operations."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.users
    
    async def create(self, user: UserDocument) -> UserDocument:
        """Create a new user."""
        result = await self.collection.insert_one(user.dict(by_alias=True))
        user.id = str(result.inserted_id)
        return user
    
    async def find_by_email(self, email: str) -> Optional[UserDocument]:
        """Find user by email."""
        doc = await self.collection.find_one({"email": email})
        return UserDocument(**doc) if doc else None
    
    async def find_by_id(self, user_id: str) -> Optional[UserDocument]:
        """Find user by ID."""
        doc = await self.collection.find_one({"_id": user_id})
        return UserDocument(**doc) if doc else None
    
    async def update(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update user fields."""
        result = await self.collection.update_one(
            {"_id": user_id},
            {"$set": updates}
        )
        return result.modified_count > 0
    
    async def update_oauth_tokens(
        self,
        user_id: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        expiry: Optional[datetime] = None
    ) -> bool:
        """Update OAuth tokens for user."""
        updates = {
            "oauth_access_token": access_token,
            "last_login": datetime.utcnow()
        }
        if refresh_token:
            updates["oauth_refresh_token"] = refresh_token
        if expiry:
            updates["oauth_token_expiry"] = expiry
        
        result = await self.collection.update_one(
            {"_id": user_id},
            {"$set": updates}
        )
        return result.modified_count > 0
    
    async def update_last_login(self, user_id: str) -> bool:
        """Update last login timestamp."""
        result = await self.collection.update_one(
            {"_id": user_id},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        return result.modified_count > 0
    
    async def update_session_token(self, user_id: str, session_token: str) -> bool:
        """Update session token for user."""
        result = await self.collection.update_one(
            {"_id": user_id},
            {"$set": {"session_token": session_token}}
        )
        return result.modified_count > 0

class EmailRepository:
    """Repository for email operations."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.emails
    
    async def create(self, email: EmailDocument) -> EmailDocument:
        """Create a new email."""
        email_dict = email.dict(by_alias=True)
        result = await self.collection.insert_one(email_dict)
        return email
    
    async def find_by_id(self, email_id: str) -> Optional[EmailDocument]:
        """Find email by ID."""
        doc = await self.collection.find_one({"_id": email_id})
        return EmailDocument(**doc) if doc else None
    
    async def find_by_flow_id(self, flow_id: str) -> Optional[EmailDocument]:
        """Find email by flow ID."""
        doc = await self.collection.find_one({"flow_id": flow_id})
        return EmailDocument(**doc) if doc else None
    
    async def find_by_gmail_id(self, gmail_message_id: str) -> Optional[EmailDocument]:
        """Find email by Gmail message ID."""
        doc = await self.collection.find_one({"gmail_message_id": gmail_message_id})
        if not doc and not gmail_message_id.startswith("gmail_"):
            prefixed_id = f"gmail_{gmail_message_id}"
            doc = await self.collection.find_one({"gmail_message_id": prefixed_id})
        return EmailDocument(**doc) if doc else None
    
    async def list_by_user(
        self,
        user_email: str,
        direction: Optional[EmailDirection] = None,
        limit: int = 50,
        skip: int = 0
    ) -> List[EmailDocument]:
        """List emails for a user."""
        query: Dict[str, Any] = {
            "$or": [
                {"sender_email": user_email},
                {"receiver_email": user_email}
            ]
        }
        if direction:
            query["direction"] = direction.value
        
        cursor = self.collection.find(query).sort("timestamp", -1).skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [EmailDocument(**doc) for doc in docs]
    
    async def update(self, email_id: str, updates: Dict[str, Any]) -> bool:
        """Update email fields."""
        result = await self.collection.update_one(
            {"_id": email_id},
            {"$set": updates}
        )
        return result.modified_count > 0
    
    async def mark_as_read(self, email_id: str) -> bool:
        """Mark email as read by _id."""
        return await self.update(email_id, {"is_read": True})
    
    async def mark_as_read_by_flow_id(self, flow_id: str) -> bool:
        """Mark email as read by flow_id."""
        result = await self.collection.update_one(
            {"flow_id": flow_id},
            {"$set": {"is_read": True}}
        )
        return result.modified_count > 0
    
    async def delete(self, email_id: str) -> bool:
        """Delete an email."""
        result = await self.collection.delete_one({"_id": email_id})
        return result.deleted_count > 0
    
    async def find_by_filter(
        self,
        filter_query: Dict[str, Any],
        limit: int = 50,
        skip: int = 0,
        sort: Optional[List[Any]] = None
    ) -> List[EmailDocument]:
        """Find emails by custom filter."""
        cursor = self.collection.find(filter_query)
        if sort:
            cursor = cursor.sort(sort)
        else:
            cursor = cursor.sort("timestamp", -1)
            
        cursor = cursor.skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [EmailDocument(**doc) for doc in docs]

    async def count_by_filter(self, filter_query: Dict[str, Any]) -> int:
        """Count emails matching filter."""
        return await self.collection.count_documents(filter_query)

class DraftRepository:
    """Repository for draft operations."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.drafts
    
    async def create(self, draft: DraftDocument) -> DraftDocument:
        """Create a new draft with comprehensive validation and error handling."""
        try:
            # Prepare document for MongoDB (use _id instead of id)
            draft_dict = draft.dict(by_alias=True, exclude_none=False)
            
            # Ensure _id exists and is properly formatted
            if '_id' not in draft_dict and 'id' in draft_dict:
                draft_dict['_id'] = draft_dict.pop('id')
            
            # Validate required fields
            if not draft_dict.get('user_id'):
                raise ValueError("user_id is required and cannot be empty")
            if not draft_dict.get('user_email'):
                raise ValueError("user_email is required and cannot be empty")
            
            logger.info(f"💾 Inserting draft into MongoDB:")
            logger.info(f"   _id: {draft_dict.get('_id')}")
            logger.info(f"   user_id: {draft_dict.get('user_id')}")
            logger.info(f"   user_email: {draft_dict.get('user_email')}")
            logger.info(f"   subject: {draft_dict.get('subject', '(no subject)')}")
            logger.info(f"   body_length: {len(draft_dict.get('body', ''))}")
            
            # Insert into MongoDB
            result = await self.collection.insert_one(draft_dict)
            
            logger.info(f"✅ MongoDB insert successful!")
            logger.info(f"   inserted_id: {result.inserted_id}")
            logger.info(f"   acknowledged: {result.acknowledged}")
            
            # Verify insertion
            verify = await self.collection.find_one({"_id": draft_dict['_id']})
            if verify:
                logger.info(f"✅ Draft verified in database: {verify.get('_id')}")
            else:
                logger.warning(f"⚠️ Draft not found after insert! This should not happen.")
            
            return draft
            
        except ValueError as ve:
            logger.error(f"❌ Validation error: {ve}")
            raise
        except Exception as e:
            logger.error(f"❌ Failed to insert draft into MongoDB: {e}")
            logger.error(f"   Draft data: {draft_dict if 'draft_dict' in locals() else 'N/A'}")
            raise
    
    async def find_by_id(self, draft_id: str) -> Optional[DraftDocument]:
        """Find draft by ID with detailed logging."""
        try:
            logger.info(f"🔍 Searching for draft with _id: {draft_id}")
            doc = await self.collection.find_one({"_id": draft_id})
            
            if doc:
                logger.info(f"✅ Draft found: subject='{doc.get('subject', '(no subject)')}'")
                return DraftDocument(**doc)
            else:
                logger.info(f"❌ Draft not found with _id: {draft_id}")
                
                # Log collection stats for debugging
                total_count = await self.collection.count_documents({})
                logger.info(f"   Total drafts in collection: {total_count}")
                
                if total_count > 0:
                    sample_drafts = await self.collection.find().limit(3).to_list(length=3)
                    sample_ids = [d.get('_id') for d in sample_drafts]
                    logger.info(f"   Sample draft IDs: {sample_ids}")
                
                return None
                
        except Exception as e:
            logger.error(f"❌ Error finding draft by ID: {e}")
            return None
    
    async def list_by_user(self, user_id: str) -> List[DraftDocument]:
        """List all drafts for a user."""
        cursor = self.collection.find({"user_id": user_id}).sort("updated_at", -1)
        docs = await cursor.to_list(length=None)
        return [DraftDocument(**doc) for doc in docs]
    
    async def list_by_email(self, user_email: str) -> List[DraftDocument]:
        """List all drafts by user email (for cross-device sync)."""
        logger.info(f"Querying drafts collection for user_email: {user_email}")
        cursor = self.collection.find({"user_email": user_email}).sort("updated_at", -1)
        docs = await cursor.to_list(length=None)
        logger.info(f"Found {len(docs)} draft documents in MongoDB for {user_email}")
        return [DraftDocument(**doc) for doc in docs]
    
    async def find_by_user_and_id(self, user_email: str, draft_id: str) -> Optional[DraftDocument]:
        """Find draft by user email and draft ID (ensures user owns the draft)."""
        doc = await self.collection.find_one({"_id": draft_id, "user_email": user_email})
        return DraftDocument(**doc) if doc else None
    
    async def update(self, draft_id: str, updates: Dict[str, Any]) -> bool:
        """Update draft fields."""
        updates["updated_at"] = datetime.utcnow()
        result = await self.collection.update_one(
            {"_id": draft_id},
            {"$set": updates}
        )
        logger.info(f"Update result - matched: {result.matched_count}, modified: {result.modified_count}")
        return result.matched_count > 0
    
    async def delete(self, draft_id: str) -> bool:
        """Delete a draft."""
        result = await self.collection.delete_one({"_id": draft_id})
        return result.deleted_count > 0

class EncryptionMetadataRepository:
    """Repository for encryption metadata operations."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.encryption_metadata
    
    async def create(self, metadata: EncryptionMetadataDocument) -> EncryptionMetadataDocument:
        """Create encryption metadata."""
        await self.collection.insert_one(metadata.dict(by_alias=True))
        return metadata
    
    async def find_by_flow_id(self, flow_id: str) -> Optional[EncryptionMetadataDocument]:
        """Find metadata by flow ID."""
        doc = await self.collection.find_one({"flow_id": flow_id})
        return EncryptionMetadataDocument(**doc) if doc else None
    
    async def find_by_email_id(self, email_id: str) -> Optional[EncryptionMetadataDocument]:
        """Find metadata by email ID."""
        doc = await self.collection.find_one({"email_id": email_id})
        return EncryptionMetadataDocument(**doc) if doc else None

class KeyUsageRepository:
    """Repository for key usage tracking."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.key_usage
    
    async def create(self, key_usage: KeyUsageDocument) -> KeyUsageDocument:
        """Record key usage."""
        await self.collection.insert_one(key_usage.dict(by_alias=True))
        return key_usage
    
    async def list_by_email(self, email_id: str) -> List[KeyUsageDocument]:
        """List key usage for an email."""
        cursor = self.collection.find({"email_id": email_id})
        docs = await cursor.to_list(length=None)
        return [KeyUsageDocument(**doc) for doc in docs]

class AttachmentRepository:
    """Repository for attachment operations."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.attachments
    
    async def create(self, attachment: AttachmentDocument) -> AttachmentDocument:
        """Create an attachment."""
        await self.collection.insert_one(attachment.dict(by_alias=True))
        return attachment
    
    async def list_by_email(self, email_id: str) -> List[AttachmentDocument]:
        """List attachments for an email."""
        cursor = self.collection.find({"email_id": email_id})
        docs = await cursor.to_list(length=None)
        return [AttachmentDocument(**doc) for doc in docs]
    
    async def update(self, attachment_id: str, updates: Dict[str, Any]) -> bool:
        """Update attachment fields."""
        result = await self.collection.update_one(
            {"_id": attachment_id},
            {"$set": updates}
        )
        return result.modified_count > 0

    async def delete(self, attachment_id: str) -> bool:
        """Delete an attachment."""
        result = await self.collection.delete_one({"_id": attachment_id})
        return result.deleted_count > 0


# ============================================================================
# QKD (Quantum Key Distribution) Repositories
# ============================================================================

class QKDKeyRepository:
    """Repository for QKD quantum key operations in MongoDB."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.qkd_keys
    
    async def create(self, key: QKDKeyDocument) -> QKDKeyDocument:
        """Store a new quantum key."""
        await self.collection.insert_one(key.dict(by_alias=True))
        logger.info(f"QKD Key stored in MongoDB: {key.key_id}")
        return key
    
    async def find_by_key_id(self, key_id: str) -> Optional[QKDKeyDocument]:
        """Find a quantum key by its key_id."""
        doc = await self.collection.find_one({"key_id": key_id})
        return QKDKeyDocument(**doc) if doc else None
    
    async def find_by_id(self, id: str) -> Optional[QKDKeyDocument]:
        """Find a quantum key by MongoDB _id."""
        doc = await self.collection.find_one({"_id": id})
        return QKDKeyDocument(**doc) if doc else None
    
    async def find_by_flow_id(self, flow_id: str) -> List[QKDKeyDocument]:
        """Find all keys associated with a flow ID."""
        cursor = self.collection.find({"flow_id": flow_id})
        docs = await cursor.to_list(length=None)
        return [QKDKeyDocument(**doc) for doc in docs]
    
    async def find_by_email_id(self, email_id: str) -> List[QKDKeyDocument]:
        """Find all keys associated with an email ID."""
        cursor = self.collection.find({"email_id": email_id})
        docs = await cursor.to_list(length=None)
        return [QKDKeyDocument(**doc) for doc in docs]
    
    async def find_available_keys(
        self, 
        security_level: int = None,
        limit: int = 10
    ) -> List[QKDKeyDocument]:
        """Find available (ready) keys, optionally filtered by security level."""
        query = {"state": QKDKeyState.READY.value, "is_consumed": False}
        if security_level:
            query["security_level"] = security_level
        
        cursor = self.collection.find(query).sort("created_at", 1).limit(limit)
        docs = await cursor.to_list(length=None)
        return [QKDKeyDocument(**doc) for doc in docs]
    
    async def find_by_sender_receiver(
        self, 
        sender_email: str, 
        receiver_email: str,
        only_available: bool = True
    ) -> List[QKDKeyDocument]:
        """Find keys for a specific sender-receiver pair."""
        query = {
            "sender_email": sender_email,
            "receiver_email": receiver_email
        }
        if only_available:
            query["state"] = QKDKeyState.READY.value
            query["is_consumed"] = False
        
        cursor = self.collection.find(query).sort("created_at", 1)
        docs = await cursor.to_list(length=None)
        return [QKDKeyDocument(**doc) for doc in docs]
    
    async def reserve_key(
        self, 
        key_id: str, 
        user_id: str,
        flow_id: str = None
    ) -> bool:
        """Reserve a key for encryption (marks it as reserved)."""
        result = await self.collection.update_one(
            {"key_id": key_id, "state": QKDKeyState.READY.value},
            {
                "$set": {
                    "state": QKDKeyState.RESERVED.value,
                    "reserved_by": user_id,
                    "reserved_at": datetime.utcnow(),
                    "flow_id": flow_id,
                    "last_accessed_at": datetime.utcnow()
                }
            }
        )
        if result.modified_count > 0:
            logger.info(f"QKD Key reserved: {key_id} by {user_id}")
        return result.modified_count > 0
    
    async def consume_key(
        self, 
        key_id: str, 
        user_id: str,
        email_id: str = None
    ) -> bool:
        """Mark a key as consumed (one-time use)."""
        result = await self.collection.update_one(
            {"key_id": key_id, "is_consumed": False},
            {
                "$set": {
                    "state": QKDKeyState.CONSUMED.value,
                    "is_consumed": True,
                    "consumed_by": user_id,
                    "consumed_at": datetime.utcnow(),
                    "email_id": email_id,
                    "last_accessed_at": datetime.utcnow()
                },
                "$push": {
                    "operation_history": {
                        "operation": "CONSUMED",
                        "user_id": user_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
            }
        )
        if result.modified_count > 0:
            logger.info(f"QKD Key consumed: {key_id} by {user_id}")
        return result.modified_count > 0
    
    async def mark_expired(self, key_id: str) -> bool:
        """Mark a key as expired."""
        result = await self.collection.update_one(
            {"key_id": key_id},
            {
                "$set": {
                    "state": QKDKeyState.EXPIRED.value,
                    "last_accessed_at": datetime.utcnow()
                }
            }
        )
        return result.modified_count > 0
    
    async def cleanup_expired_keys(self) -> int:
        """Remove or mark expired keys. Returns count of affected keys."""
        now = datetime.utcnow()
        result = await self.collection.update_many(
            {
                "expires_at": {"$lt": now},
                "state": {"$nin": [QKDKeyState.CONSUMED.value, QKDKeyState.EXPIRED.value]}
            },
            {"$set": {"state": QKDKeyState.EXPIRED.value}}
        )
        if result.modified_count > 0:
            logger.info(f"Marked {result.modified_count} QKD keys as expired")
        return result.modified_count
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get QKD key pool statistics."""
        pipeline = [
            {
                "$group": {
                    "_id": "$state",
                    "count": {"$sum": 1}
                }
            }
        ]
        cursor = self.collection.aggregate(pipeline)
        stats = await cursor.to_list(length=None)
        
        result = {
            "ready": 0,
            "reserved": 0,
            "consumed": 0,
            "expired": 0,
            "total": 0
        }
        for stat in stats:
            state = stat["_id"]
            count = stat["count"]
            result[state] = count
            result["total"] += count
        
        return result
    
    async def get_keys_by_user(
        self, 
        user_email: str, 
        include_consumed: bool = False
    ) -> List[QKDKeyDocument]:
        """Get all keys associated with a user (as sender or receiver)."""
        query = {
            "$or": [
                {"sender_email": user_email},
                {"receiver_email": user_email}
            ]
        }
        if not include_consumed:
            query["is_consumed"] = False
        
        cursor = self.collection.find(query).sort("created_at", -1)
        docs = await cursor.to_list(length=None)
        return [QKDKeyDocument(**doc) for doc in docs]


class QKDSessionRepository:
    """Repository for QKD session operations in MongoDB."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.qkd_sessions
    
    async def create(self, session: QKDSessionDocument) -> QKDSessionDocument:
        """Create a new QKD session."""
        await self.collection.insert_one(session.dict(by_alias=True))
        logger.info(f"QKD Session created: {session.session_id}")
        return session
    
    async def find_by_session_id(self, session_id: str) -> Optional[QKDSessionDocument]:
        """Find a session by session_id."""
        doc = await self.collection.find_one({"session_id": session_id})
        return QKDSessionDocument(**doc) if doc else None
    
    async def find_by_flow_id(self, flow_id: str) -> Optional[QKDSessionDocument]:
        """Find a session by flow_id."""
        doc = await self.collection.find_one({"flow_id": flow_id})
        return QKDSessionDocument(**doc) if doc else None
    
    async def find_active_sessions(
        self, 
        user_email: str = None
    ) -> List[QKDSessionDocument]:
        """Find active sessions, optionally filtered by user."""
        query = {"is_active": True}
        if user_email:
            query["$or"] = [
                {"sender_email": user_email},
                {"receiver_email": user_email}
            ]
        
        cursor = self.collection.find(query).sort("started_at", -1)
        docs = await cursor.to_list(length=None)
        return [QKDSessionDocument(**doc) for doc in docs]
    
    async def complete_session(
        self, 
        session_id: str, 
        success: bool = True,
        error_message: str = None
    ) -> bool:
        """Mark a session as completed."""
        result = await self.collection.update_one(
            {"session_id": session_id},
            {
                "$set": {
                    "is_active": False,
                    "is_successful": success,
                    "completed_at": datetime.utcnow(),
                    "error_message": error_message
                }
            }
        )
        return result.modified_count > 0
    
    async def add_key_to_session(
        self, 
        session_id: str, 
        key_id: str,
        key_size_bits: int = 256
    ) -> bool:
        """Add a key to a session's key list."""
        result = await self.collection.update_one(
            {"session_id": session_id},
            {
                "$push": {"key_ids": key_id},
                "$inc": {
                    "total_keys_used": 1,
                    "total_bits_exchanged": key_size_bits
                }
            }
        )
        return result.modified_count > 0
    
    async def get_session_statistics(self) -> Dict[str, Any]:
        """Get QKD session statistics."""
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total_sessions": {"$sum": 1},
                    "active_sessions": {
                        "$sum": {"$cond": ["$is_active", 1, 0]}
                    },
                    "successful_sessions": {
                        "$sum": {"$cond": ["$is_successful", 1, 0]}
                    },
                    "total_keys_used": {"$sum": "$total_keys_used"},
                    "total_bits_exchanged": {"$sum": "$total_bits_exchanged"}
                }
            }
        ]
        cursor = self.collection.aggregate(pipeline)
        stats = await cursor.to_list(length=1)
        
        if stats:
            return stats[0]
        return {
            "total_sessions": 0,
            "active_sessions": 0,
            "successful_sessions": 0,
            "total_keys_used": 0,
            "total_bits_exchanged": 0
        }


class QKDAuditLogRepository:
    """Repository for QKD audit log operations in MongoDB."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.qkd_audit_logs
    
    async def create(self, log: QKDAuditLogDocument) -> QKDAuditLogDocument:
        """Create a new audit log entry."""
        await self.collection.insert_one(log.dict(by_alias=True))
        return log
    
    async def log_operation(
        self,
        operation: str,
        key_id: str = None,
        session_id: str = None,
        flow_id: str = None,
        user_email: str = None,
        user_id: str = None,
        success: bool = True,
        error_message: str = None,
        details: Dict[str, Any] = None,
        severity: str = "INFO"
    ) -> QKDAuditLogDocument:
        """Convenience method to log a QKD operation."""
        log = QKDAuditLogDocument(
            operation=operation,
            key_id=key_id,
            session_id=session_id,
            flow_id=flow_id,
            user_email=user_email,
            user_id=user_id,
            success=success,
            error_message=error_message,
            details=details,
            severity=severity
        )
        return await self.create(log)
    
    async def find_by_key_id(self, key_id: str) -> List[QKDAuditLogDocument]:
        """Find all audit logs for a specific key."""
        cursor = self.collection.find({"key_id": key_id}).sort("timestamp", -1)
        docs = await cursor.to_list(length=None)
        return [QKDAuditLogDocument(**doc) for doc in docs]
    
    async def find_by_session_id(self, session_id: str) -> List[QKDAuditLogDocument]:
        """Find all audit logs for a specific session."""
        cursor = self.collection.find({"session_id": session_id}).sort("timestamp", -1)
        docs = await cursor.to_list(length=None)
        return [QKDAuditLogDocument(**doc) for doc in docs]
    
    async def find_by_user(
        self, 
        user_email: str, 
        limit: int = 100
    ) -> List[QKDAuditLogDocument]:
        """Find audit logs for a specific user."""
        cursor = self.collection.find(
            {"user_email": user_email}
        ).sort("timestamp", -1).limit(limit)
        docs = await cursor.to_list(length=None)
        return [QKDAuditLogDocument(**doc) for doc in docs]
    
    async def find_by_operation(
        self, 
        operation: str, 
        limit: int = 100
    ) -> List[QKDAuditLogDocument]:
        """Find audit logs by operation type."""
        cursor = self.collection.find(
            {"operation": operation}
        ).sort("timestamp", -1).limit(limit)
        docs = await cursor.to_list(length=None)
        return [QKDAuditLogDocument(**doc) for doc in docs]
    
    async def find_errors(self, limit: int = 100) -> List[QKDAuditLogDocument]:
        """Find failed operations."""
        cursor = self.collection.find(
            {"success": False}
        ).sort("timestamp", -1).limit(limit)
        docs = await cursor.to_list(length=None)
        return [QKDAuditLogDocument(**doc) for doc in docs]
    
    async def find_recent(
        self, 
        hours: int = 24, 
        limit: int = 100
    ) -> List[QKDAuditLogDocument]:
        """Find recent audit logs."""
        since = datetime.utcnow() - timedelta(hours=hours)
        cursor = self.collection.find(
            {"timestamp": {"$gte": since}}
        ).sort("timestamp", -1).limit(limit)
        docs = await cursor.to_list(length=None)
        return [QKDAuditLogDocument(**doc) for doc in docs]


class QKDKeyPoolStatusRepository:
    """Repository for QKD key pool status monitoring in MongoDB."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.qkd_pool_status
    
    async def upsert(self, status: QKDKeyPoolStatusDocument) -> QKDKeyPoolStatusDocument:
        """Create or update pool status."""
        status.updated_at = datetime.utcnow()
        await self.collection.update_one(
            {"kme_id": status.kme_id, "sae_id": status.sae_id},
            {"$set": status.dict(by_alias=True)},
            upsert=True
        )
        return status
    
    async def find_by_kme(self, kme_id: str) -> Optional[QKDKeyPoolStatusDocument]:
        """Find pool status for a specific KME."""
        doc = await self.collection.find_one({"kme_id": kme_id})
        return QKDKeyPoolStatusDocument(**doc) if doc else None
    
    async def get_all_status(self) -> List[QKDKeyPoolStatusDocument]:
        """Get status for all key pools."""
        cursor = self.collection.find({})
        docs = await cursor.to_list(length=None)
        return [QKDKeyPoolStatusDocument(**doc) for doc in docs]
    
    async def update_key_counts(
        self,
        kme_id: str,
        available: int = None,
        reserved: int = None,
        consumed: int = None,
        expired: int = None
    ) -> bool:
        """Update key counts for a pool."""
        updates = {"updated_at": datetime.utcnow()}
        if available is not None:
            updates["available_keys"] = available
        if reserved is not None:
            updates["reserved_keys"] = reserved
        if consumed is not None:
            updates["consumed_keys"] = consumed
        if expired is not None:
            updates["expired_keys"] = expired
        
        result = await self.collection.update_one(
            {"kme_id": kme_id},
            {"$set": updates}
        )
        return result.modified_count > 0
    
    async def record_key_generated(self, kme_id: str) -> bool:
        """Record that a key was generated."""
        result = await self.collection.update_one(
            {"kme_id": kme_id},
            {
                "$set": {"last_key_generated": datetime.utcnow()},
                "$inc": {"available_keys": 1, "total_keys": 1}
            }
        )
        return result.modified_count > 0
    
    async def record_key_consumed(self, kme_id: str) -> bool:
        """Record that a key was consumed."""
        result = await self.collection.update_one(
            {"kme_id": kme_id},
            {
                "$set": {"last_key_consumed": datetime.utcnow()},
                "$inc": {"consumed_keys": 1, "available_keys": -1}
            }
        )
        return result.modified_count > 0
    
    async def update_health_status(
        self, 
        kme_id: str, 
        is_healthy: bool,
        error_count: int = None
    ) -> bool:
        """Update health status for a pool."""
        updates = {
            "is_healthy": is_healthy,
            "last_health_check": datetime.utcnow()
        }
        if error_count is not None:
            updates["error_count"] = error_count
        
        result = await self.collection.update_one(
            {"kme_id": kme_id},
            {"$set": updates}
        )
        return result.modified_count > 0
