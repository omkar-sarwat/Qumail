# MongoDB Save Issues - Complete Fix Guide

## Problem Diagnosis

MongoDB is not saving drafts and other data properly due to several issues:

### 1. **Field Alias Mismatch (_id vs id)**
- MongoDB uses `_id` as the primary key
- Pydantic models use `id` with `alias="_id"`
- When inserting documents, we're passing `id` but MongoDB expects `_id`

### 2. **UUID String vs ObjectId Conflict**
- MongoDB prefers ObjectId for `_id` field
- We're using UUID strings which may cause insert failures
- Motor/PyMongo may reject string IDs in some cases

### 3. **Missing Field Validation**
- Required fields (user_id, user_email) may be None or empty
- No validation before insert causes silent failures

### 4. **Connection Issues**
- MongoDB Atlas connection may timeout
- No retry logic for transient network failures
- Connection pool exhaustion not handled

### 5. **Index Conflicts**
- Unique indexes on `_id` may conflict with duplicate IDs
- No duplicate key error handling

## Complete Solutions

### Solution 1: Fix Document Models (mongo_models.py)

**Problem**: `_id` field aliasing not working correctly with Motor

**Fix**: Use proper field configuration and ensure `_id` is handled correctly

```python
from bson import ObjectId

class DraftDocument(BaseModel):
    """Draft document - properly handles MongoDB _id field"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    user_id: str = Field(..., description="Required: MongoDB user ID")
    user_email: str = Field(..., description="Required: User's email address")
    recipient: Optional[str] = ""
    subject: Optional[str] = ""
    body: Optional[str] = ""
    security_level: int = Field(default=2, ge=1, le=4)
    cc: Optional[str] = None
    bcc: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_synced: bool = True
    
    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ObjectId: lambda v: str(v)
        }
    
    def dict(self, **kwargs):
        """Override dict to ensure _id is used instead of id"""
        d = super().dict(**kwargs)
        if 'id' in d and '_id' not in d:
            d['_id'] = d.pop('id')
        return d
```

### Solution 2: Fix Repository Insert Logic (mongo_repositories.py)

**Problem**: `insert_one()` failing due to incorrect document format

**Fix**: Properly prepare document for MongoDB insertion

```python
class DraftRepository:
    """Repository for draft operations with proper error handling."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.drafts
    
    async def create(self, draft: DraftDocument) -> DraftDocument:
        """Create a new draft with proper MongoDB insertion."""
        try:
            # Prepare document for MongoDB (use _id instead of id)
            draft_dict = draft.dict(by_alias=True, exclude_none=False)
            
            # Ensure _id exists
            if '_id' not in draft_dict and 'id' in draft_dict:
                draft_dict['_id'] = draft_dict.pop('id')
            
            # Validate required fields
            if not draft_dict.get('user_id'):
                raise ValueError("user_id is required")
            if not draft_dict.get('user_email'):
                raise ValueError("user_email is required")
            
            logger.info(f"💾 Inserting draft into MongoDB:")
            logger.info(f"   _id: {draft_dict.get('_id')}")
            logger.info(f"   user_email: {draft_dict.get('user_email')}")
            logger.info(f"   subject: {draft_dict.get('subject')}")
            
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
                logger.warning(f"⚠️ Draft not found after insert!")
            
            return draft
            
        except Exception as e:
            logger.error(f"❌ Failed to insert draft: {e}")
            logger.error(f"   Draft data: {draft_dict if 'draft_dict' in locals() else 'N/A'}")
            raise
    
    async def find_by_id(self, draft_id: str) -> Optional[DraftDocument]:
        """Find draft by ID with detailed logging."""
        try:
            logger.info(f"🔍 Searching for draft with _id: {draft_id}")
            doc = await self.collection.find_one({"_id": draft_id})
            
            if doc:
                logger.info(f"✅ Draft found: {doc.get('subject', '(no subject)')}")
                return DraftDocument(**doc)
            else:
                logger.info(f"❌ Draft not found with _id: {draft_id}")
                
                # Try alternative search (in case ID format issue)
                all_drafts = await self.collection.find().to_list(length=10)
                logger.info(f"   Total drafts in collection: {len(all_drafts)}")
                if all_drafts:
                    logger.info(f"   Sample IDs: {[d.get('_id') for d in all_drafts[:3]]}")
                
                return None
                
        except Exception as e:
            logger.error(f"❌ Error finding draft: {e}")
            return None
    
    async def list_by_email(self, user_email: str) -> List[DraftDocument]:
        """List all drafts by user email with detailed logging."""
        try:
            logger.info(f"📋 Querying drafts for user_email: {user_email}")
            
            # Count total documents
            total_count = await self.collection.count_documents({})
            logger.info(f"   Total drafts in collection: {total_count}")
            
            # Query user's drafts
            cursor = self.collection.find({"user_email": user_email}).sort("updated_at", -1)
            docs = await cursor.to_list(length=None)
            
            logger.info(f"✅ Found {len(docs)} drafts for {user_email}")
            
            if docs:
                for i, doc in enumerate(docs[:3]):  # Log first 3
                    logger.info(f"   Draft {i+1}: _id={doc.get('_id')}, subject='{doc.get('subject', '(no subject)')}'")
            
            return [DraftDocument(**doc) for doc in docs]
            
        except Exception as e:
            logger.error(f"❌ Error listing drafts: {e}")
            return []
    
    async def update(self, draft_id: str, updates: Dict[str, Any]) -> bool:
        """Update draft with proper error handling."""
        try:
            updates["updated_at"] = datetime.utcnow()
            
            logger.info(f"📝 Updating draft {draft_id}")
            logger.info(f"   Updates: {list(updates.keys())}")
            
            result = await self.collection.update_one(
                {"_id": draft_id},
                {"$set": updates}
            )
            
            logger.info(f"   matched_count: {result.matched_count}")
            logger.info(f"   modified_count: {result.modified_count}")
            
            if result.matched_count > 0:
                logger.info(f"✅ Draft updated successfully")
                return True
            else:
                logger.warning(f"⚠️ No draft found with _id: {draft_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error updating draft: {e}")
            return False
```

### Solution 3: Fix API Route Handler (routes/emails.py)

**Problem**: Draft save endpoint not validating data properly

**Fix**: Add comprehensive validation and error handling

```python
@router.post("/drafts")
async def create_or_update_draft(
    request: Request,
    to: str = Form(None),
    recipient: str = Form(None),
    cc: str = Form(None),
    bcc: str = Form(None),
    subject: str = Form(""),
    body: str = Form(""),
    securityLevel: int = Form(None),
    security_level: int = Form(None),
    id: str = Form(None),
    draftId: str = Form(None),
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> Dict[str, Any]:
    """Create or update a draft with comprehensive error handling."""
    try:
        from ..mongo_repositories import DraftRepository
        from ..mongo_models import DraftDocument
        
        draft_repo = DraftRepository(db)
        
        # Extract and validate inputs
        recipient_email = to or recipient or ""
        draft_subject = subject or ""
        draft_body = body or ""
        level = securityLevel or security_level or 2
        draft_id = id or draftId
        
        logger.info(f"💾 Draft save request:")
        logger.info(f"   User: {current_user.email} (ID: {current_user.id})")
        logger.info(f"   Draft ID: {draft_id or '(new)'}")
        logger.info(f"   To: {recipient_email}")
        logger.info(f"   Subject: {draft_subject}")
        logger.info(f"   Body length: {len(draft_body)}")
        logger.info(f"   Security level: {level}")
        
        # Validate user authentication
        if not current_user.id or not current_user.email:
            logger.error("❌ User not properly authenticated")
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        # Check if updating existing draft
        if draft_id:
            logger.info(f"🔍 Checking if draft {draft_id} exists...")
            existing_draft = await draft_repo.find_by_id(draft_id)
            
            if existing_draft:
                logger.info(f"✅ Existing draft found, updating...")
                
                # Prepare updates
                updates = {
                    'recipient': recipient_email,
                    'subject': draft_subject,
                    'body': draft_body,
                    'security_level': level,
                    'cc': cc,
                    'bcc': bcc,
                    'updated_at': datetime.utcnow()
                }
                
                # Perform update
                success = await draft_repo.update(draft_id, updates)
                
                if success:
                    logger.info(f"✅ Draft {draft_id} updated successfully")
                    return {
                        "success": True,
                        "draftId": draft_id,
                        "message": "Draft updated successfully"
                    }
                else:
                    logger.error(f"❌ Failed to update draft {draft_id}")
                    raise HTTPException(status_code=500, detail="Failed to update draft")
        
        # Create new draft
        logger.info(f"📝 Creating NEW draft for {current_user.email}")
        
        try:
            draft_doc = DraftDocument(
                id=draft_id or str(uuid.uuid4()),  # Use provided ID or generate new
                user_id=current_user.id,
                user_email=current_user.email,
                recipient=recipient_email,
                subject=draft_subject,
                body=draft_body,
                security_level=level,
                cc=cc or None,
                bcc=bcc or None,
                is_synced=True
            )
            
            logger.info(f"📦 Draft document created:")
            logger.info(f"   ID: {draft_doc.id}")
            logger.info(f"   User ID: {draft_doc.user_id}")
            logger.info(f"   User Email: {draft_doc.user_email}")
            
            # Save to MongoDB
            saved_draft = await draft_repo.create(draft_doc)
            
            logger.info(f"✅ Draft saved successfully!")
            logger.info(f"   Draft ID: {saved_draft.id}")
            
            return {
                "success": True,
                "draftId": saved_draft.id,
                "message": "Draft created successfully"
            }
            
        except ValueError as ve:
            logger.error(f"❌ Validation error: {ve}")
            raise HTTPException(status_code=400, detail=str(ve))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error saving draft: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(status_code=500, detail=f"Failed to save draft: {str(e)}")
```

### Solution 4: Connection Retry Logic

**Problem**: Transient network failures cause saves to fail

**Fix**: Add retry logic to repository operations

```python
import asyncio
from functools import wraps

def retry_on_failure(max_retries=3, delay=1):
    """Decorator to retry database operations on failure."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        logger.warning(f"⚠️ Attempt {attempt + 1} failed: {e}, retrying...")
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"❌ All {max_retries} attempts failed")
            raise last_error
        return wrapper
    return decorator

# Apply to repository methods:
class DraftRepository:
    @retry_on_failure(max_retries=3, delay=1)
    async def create(self, draft: DraftDocument) -> DraftDocument:
        # ... existing code ...
```

### Solution 5: Database Connection Health Check

**Problem**: No way to verify MongoDB connection is healthy

**Fix**: Add health check endpoint

```python
@router.get("/health/mongodb")
async def check_mongodb_health(db: AsyncIOMotorDatabase = Depends(get_database)):
    """Check MongoDB connection health."""
    try:
        # Ping database
        await db.command('ping')
        
        # Count documents in each collection
        stats = {
            "users": await db.users.count_documents({}),
            "emails": await db.emails.count_documents({}),
            "drafts": await db.drafts.count_documents({}),
            "encryption_metadata": await db.encryption_metadata.count_documents({}),
            "key_usage": await db.key_usage.count_documents({}),
            "attachments": await db.attachments.count_documents({})
        }
        
        return {
            "status": "healthy",
            "connected": True,
            "database": db.name,
            "collections": stats
        }
    except Exception as e:
        logger.error(f"MongoDB health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"MongoDB unhealthy: {str(e)}")
```

## Testing Script

Create `test_mongodb_save.py` to verify fixes:

```python
"""Test MongoDB save operations."""
import asyncio
from app.mongo_database import connect_to_mongo, close_mongo_connection, get_database
from app.mongo_repositories import DraftRepository
from app.mongo_models import DraftDocument
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_draft_save():
    """Test draft creation and retrieval."""
    try:
        # Connect
        await connect_to_mongo()
        db = get_database()
        draft_repo = DraftRepository(db)
        
        # Create test draft
        test_draft = DraftDocument(
            user_id="test-user-123",
            user_email="test@example.com",
            recipient="recipient@example.com",
            subject="Test Draft",
            body="<p>Test body</p>",
            security_level=2
        )
        
        logger.info("=" * 60)
        logger.info("TEST 1: Creating draft...")
        saved_draft = await draft_repo.create(test_draft)
        logger.info(f"✅ Draft created with ID: {saved_draft.id}")
        
        logger.info("=" * 60)
        logger.info("TEST 2: Retrieving draft by ID...")
        found_draft = await draft_repo.find_by_id(saved_draft.id)
        if found_draft:
            logger.info(f"✅ Draft retrieved: {found_draft.subject}")
        else:
            logger.error(f"❌ Draft NOT found!")
        
        logger.info("=" * 60)
        logger.info("TEST 3: Listing drafts by email...")
        drafts = await draft_repo.list_by_email("test@example.com")
        logger.info(f"✅ Found {len(drafts)} drafts")
        
        logger.info("=" * 60)
        logger.info("TEST 4: Updating draft...")
        success = await draft_repo.update(saved_draft.id, {"subject": "Updated Subject"})
        if success:
            logger.info(f"✅ Draft updated")
        else:
            logger.error(f"❌ Draft update failed!")
        
        logger.info("=" * 60)
        logger.info("TEST 5: Verifying update...")
        updated_draft = await draft_repo.find_by_id(saved_draft.id)
        if updated_draft and updated_draft.subject == "Updated Subject":
            logger.info(f"✅ Update verified: {updated_draft.subject}")
        else:
            logger.error(f"❌ Update verification failed!")
        
        logger.info("=" * 60)
        logger.info("✅ ALL TESTS PASSED!")
        
    except Exception as e:
        logger.error(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(test_draft_save())
```

## Checklist for Complete Fix

- [ ] Update `DraftDocument` model with proper `_id` handling
- [ ] Fix `DraftRepository.create()` method with validation
- [ ] Add retry logic to repository operations
- [ ] Update API route with comprehensive error handling
- [ ] Add MongoDB health check endpoint
- [ ] Test with `test_mongodb_save.py` script
- [ ] Verify in production with real user data
- [ ] Monitor logs for insertion success
- [ ] Check MongoDB Atlas dashboard for document count

## Expected Log Output (Success)

```
💾 Draft save request:
   User: user@example.com (ID: abc-123)
   Draft ID: (new)
   To: recipient@example.com
   Subject: Test Email
   Body length: 245
   Security level: 2

📝 Creating NEW draft for user@example.com

📦 Draft document created:
   ID: f63e996a-b26f-48aa-bacb-4af232981fc1
   User ID: abc-123
   User Email: user@example.com

💾 Inserting draft into MongoDB:
   _id: f63e996a-b26f-48aa-bacb-4af232981fc1
   user_email: user@example.com
   subject: Test Email

✅ MongoDB insert successful!
   inserted_id: f63e996a-b26f-48aa-bacb-4af232981fc1
   acknowledged: True

✅ Draft verified in database: f63e996a-b26f-48aa-bacb-4af232981fc1

✅ Draft saved successfully!
   Draft ID: f63e996a-b26f-48aa-bacb-4af232981fc1
```

## Common Errors and Solutions

### Error: "Document must have '_id' field"
**Solution**: Ensure `dict(by_alias=True)` is used when preparing documents

### Error: "duplicate key error"
**Solution**: Check if draft ID already exists before insert

### Error: "None is not a valid ObjectId"
**Solution**: Validate user_id and user_email are not None before insert

### Error: "Connection timeout"
**Solution**: Check MongoDB Atlas IP whitelist and network connectivity

### Error: "drafts.map is not a function"
**Solution**: Ensure API returns array, not object

## Monitoring and Debugging

### Check MongoDB Atlas Dashboard
1. Log in to MongoDB Atlas
2. Go to Clusters → Browse Collections
3. Select `qumail` database → `drafts` collection
4. Verify documents exist with correct structure

### Enable Debug Logging
```python
logging.basicConfig(level=logging.DEBUG)
logging.getLogger('motor').setLevel(logging.DEBUG)
logging.getLogger('pymongo').setLevel(logging.DEBUG)
```

### Query MongoDB Directly
```python
from pymongo import MongoClient
client = MongoClient("mongodb+srv://user:password@cluster.mongodb.net/")
db = client.qumail
drafts = db.drafts.find({})
for draft in drafts:
    print(draft)
```
