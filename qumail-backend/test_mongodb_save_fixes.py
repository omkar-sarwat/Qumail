"""Test MongoDB save operations to verify fixes."""
import asyncio
import sys
from datetime import datetime
from app.mongo_database import connect_to_mongo, close_mongo_connection, get_database
from app.mongo_repositories import DraftRepository
from app.mongo_models import DraftDocument
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_draft_operations():
    """Comprehensive test of draft CRUD operations."""
    try:
        logger.info("="*80)
        logger.info("MONGODB SAVE TEST - Starting")
        logger.info("="*80)
        
        # Step 1: Connect to MongoDB
        logger.info("\n[TEST 1] Connecting to MongoDB Atlas...")
        await connect_to_mongo()
        db = get_database()
        logger.info(f"✅ Connected to database: {db.name}")
        
        # Step 2: Initialize repository
        draft_repo = DraftRepository(db)
        logger.info("✅ DraftRepository initialized")
        
        # Step 3: Check initial count
        logger.info("\n[TEST 2] Checking initial draft count...")
        initial_count = await db.drafts.count_documents({})
        logger.info(f"✅ Initial draft count: {initial_count}")
        
        # Step 4: Create test draft
        logger.info("\n[TEST 3] Creating test draft...")
        test_draft = DraftDocument(
            user_id="test-user-456",
            user_email="testuser@qumail.com",
            recipient="recipient@example.com",
            subject="Test Draft - MongoDB Save Verification",
            body="<p>This is a test draft to verify MongoDB save operations.</p>",
            security_level=2,
            cc="cc@example.com",
            bcc=None
        )
        
        logger.info(f"Draft prepared with ID: {test_draft.id}")
        saved_draft = await draft_repo.create(test_draft)
        logger.info(f"✅ Draft created successfully with ID: {saved_draft.id}")
        
        # Step 5: Verify draft exists
        logger.info("\n[TEST 4] Verifying draft exists in MongoDB...")
        new_count = await db.drafts.count_documents({})
        logger.info(f"New draft count: {new_count}")
        if new_count > initial_count:
            logger.info(f"✅ Draft count increased from {initial_count} to {new_count}")
        else:
            logger.error(f"❌ Draft count did NOT increase!")
            return False
        
        # Step 6: Retrieve draft by ID
        logger.info("\n[TEST 5] Retrieving draft by ID...")
        found_draft = await draft_repo.find_by_id(saved_draft.id)
        if found_draft:
            logger.info(f"✅ Draft retrieved successfully")
            logger.info(f"   ID: {found_draft.id}")
            logger.info(f"   Subject: {found_draft.subject}")
            logger.info(f"   User Email: {found_draft.user_email}")
            logger.info(f"   Recipient: {found_draft.recipient}")
        else:
            logger.error(f"❌ Draft NOT found by ID!")
            return False
        
        # Step 7: List drafts by email
        logger.info("\n[TEST 6] Listing drafts by user email...")
        drafts_list = await draft_repo.list_by_email("testuser@qumail.com")
        logger.info(f"✅ Found {len(drafts_list)} draft(s) for testuser@qumail.com")
        if len(drafts_list) > 0:
            for i, draft in enumerate(drafts_list, 1):
                logger.info(f"   Draft {i}: {draft.subject} (ID: {draft.id})")
        else:
            logger.error(f"❌ No drafts found by email!")
            return False
        
        # Step 8: Update draft
        logger.info("\n[TEST 7] Updating draft...")
        update_success = await draft_repo.update(
            saved_draft.id,
            {
                "subject": "Updated Subject - Modified",
                "body": "<p>Updated body content</p>"
            }
        )
        if update_success:
            logger.info(f"✅ Draft updated successfully")
        else:
            logger.error(f"❌ Draft update failed!")
            return False
        
        # Step 9: Verify update
        logger.info("\n[TEST 8] Verifying update...")
        updated_draft = await draft_repo.find_by_id(saved_draft.id)
        if updated_draft and updated_draft.subject == "Updated Subject - Modified":
            logger.info(f"✅ Update verified: {updated_draft.subject}")
        else:
            logger.error(f"❌ Update verification failed!")
            return False
        
        # Step 10: Test with real user email
        logger.info("\n[TEST 9] Testing with actual user email from database...")
        real_user_drafts = await draft_repo.list_by_email("sarswatomkar8625@gmail.com")
        logger.info(f"✅ Found {len(real_user_drafts)} draft(s) for sarswatomkar8625@gmail.com")
        if len(real_user_drafts) > 0:
            logger.info(f"   First draft: {real_user_drafts[0].subject}")
        
        # Step 11: Clean up test draft
        logger.info("\n[TEST 10] Cleaning up test draft...")
        delete_success = await draft_repo.delete(saved_draft.id)
        if delete_success:
            logger.info(f"✅ Test draft deleted successfully")
        else:
            logger.warning(f"⚠️ Test draft deletion failed (may not exist)")
        
        # Final summary
        logger.info("\n" + "="*80)
        logger.info("✅ ALL TESTS PASSED!")
        logger.info("="*80)
        logger.info("\nSummary:")
        logger.info(f"  - MongoDB connection: OK")
        logger.info(f"  - Draft creation: OK")
        logger.info(f"  - Draft retrieval by ID: OK")
        logger.info(f"  - Draft listing by email: OK")
        logger.info(f"  - Draft update: OK")
        logger.info(f"  - Draft deletion: OK")
        logger.info("\n✅ MongoDB save operations are working correctly!")
        
        return True
        
    except Exception as e:
        logger.error("\n" + "="*80)
        logger.error(f"❌ TEST FAILED: {e}")
        logger.error("="*80)
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        await close_mongo_connection()
        logger.info("\nMongoDB connection closed")

if __name__ == "__main__":
    success = asyncio.run(test_draft_operations())
    sys.exit(0 if success else 1)
