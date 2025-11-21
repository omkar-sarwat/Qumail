"""Repository pattern for MongoDB data access."""
from typing import Optional, List, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from .mongo_models import (
    UserDocument,
    EmailDocument,
    DraftDocument,
    EncryptionMetadataDocument,
    KeyUsageDocument,
    AttachmentDocument,
    EmailDirection
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
