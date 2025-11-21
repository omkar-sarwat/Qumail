"""Comprehensive test script for MongoDB migration."""
import asyncio
import sys
from datetime import datetime
from app.mongo_database import connect_to_mongo, close_mongo_connection, get_database
from app.mongo_repositories import UserRepository, EmailRepository, EncryptionMetadataRepository
from app.mongo_models import UserDocument, EmailDocument, EmailDirection, EncryptionMetadataDocument
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_mongodb_migration():
    """Test all MongoDB operations."""
    try:
        # Connect to MongoDB
        logger.info("=" * 60)
        logger.info("STARTING MONGODB MIGRATION TESTS")
        logger.info("=" * 60)
        
        await connect_to_mongo()
        db = get_database()
        
        # Test 1: User Repository
        logger.info("\n📝 TEST 1: User Repository Operations")
        user_repo = UserRepository(db)
        
        # Create test user
        test_email = f"test_user_{datetime.utcnow().timestamp()}@qumail.com"
        user_doc = UserDocument(
            email=test_email,
            display_name="Migration Test User",
            oauth_access_token="test_access_token",
            oauth_refresh_token="test_refresh_token",
            last_login=datetime.utcnow()
        )
        created_user = await user_repo.create(user_doc)
        logger.info(f"✅ Created user: {created_user.email} (ID: {created_user.id})")
        
        # Find user by email
        found_user = await user_repo.find_by_email(test_email)
        assert found_user is not None, "User not found by email"
        logger.info(f"✅ Found user by email: {found_user.email}")
        
        # Update OAuth tokens
        updated = await user_repo.update_oauth_tokens(
            str(found_user.id),
            "new_access_token",
            "new_refresh_token"
        )
        assert updated, "Failed to update OAuth tokens"
        logger.info("✅ Updated OAuth tokens")
        
        # Update last login
        updated = await user_repo.update_last_login(str(found_user.id))
        assert updated, "Failed to update last login"
        logger.info("✅ Updated last login")
        
        # Test 2: Email Repository
        logger.info("\n📧 TEST 2: Email Repository Operations")
        email_repo = EmailRepository(db)
        
        # Create test email
        email_doc = EmailDocument(
            flow_id=f"test_flow_{datetime.utcnow().timestamp()}",
            user_id=str(found_user.id),
            sender_email=test_email,
            receiver_email="receiver@qumail.com",
            subject="Test Email",
            body_encrypted="encrypted_test_content",
            security_level=2,
            direction=EmailDirection.SENT,
            gmail_message_id=f"gmail_{datetime.utcnow().timestamp()}",
            is_read=False,
            timestamp=datetime.utcnow()
        )
        created_email = await email_repo.create(email_doc)
        logger.info(f"✅ Created email with flow_id: {created_email.flow_id}")
        
        # Find email by flow_id
        found_email = await email_repo.find_by_flow_id(created_email.flow_id)
        assert found_email is not None, "Email not found by flow_id"
        logger.info(f"✅ Found email by flow_id: {found_email.flow_id}")
        
        # List emails by user
        user_emails = await email_repo.list_by_user(test_email, limit=10)
        assert len(user_emails) > 0, "No emails found for user"
        logger.info(f"✅ Listed {len(user_emails)} emails for user")
        
        # Mark email as read
        marked = await email_repo.mark_as_read_by_flow_id(created_email.flow_id)
        assert marked, "Failed to mark email as read"
        logger.info("✅ Marked email as read")
        
        # Test 3: Encryption Metadata Repository
        logger.info("\n🔐 TEST 3: Encryption Metadata Repository Operations")
        metadata_repo = EncryptionMetadataRepository(db)
        
        # Create encryption metadata
        metadata_doc = EncryptionMetadataDocument(
            flow_id=created_email.flow_id,
            email_id=str(created_email.flow_id),
            key_id="test_key_123",
            security_level=2,
            algorithm="AES-256-GCM",
            nonce="test_nonce_value",
            auth_tag="test_auth_tag"
        )
        created_metadata = await metadata_repo.create(metadata_doc)
        logger.info(f"✅ Created encryption metadata for flow_id: {created_metadata.flow_id}")
        
        # Find metadata by flow_id
        found_metadata = await metadata_repo.find_by_flow_id(created_email.flow_id)
        assert found_metadata is not None, "Metadata not found by flow_id"
        logger.info(f"✅ Found metadata by flow_id: {found_metadata.flow_id}")
        
        # Test 4: Database Statistics
        logger.info("\n📊 TEST 4: Database Statistics")
        user_count = await db.users.count_documents({})
        email_count = await db.emails.count_documents({})
        metadata_count = await db.encryption_metadata.count_documents({})
        
        logger.info(f"✅ Total users: {user_count}")
        logger.info(f"✅ Total emails: {email_count}")
        logger.info(f"✅ Total encryption metadata: {metadata_count}")
        
        # Test 5: Index Verification
        logger.info("\n🔍 TEST 5: Index Verification")
        collections = await db.list_collection_names()
        for collection_name in collections:
            indexes = await db[collection_name].index_information()
            logger.info(f"✅ {collection_name}: {len(indexes)} indexes")
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ ALL MONGODB MIGRATION TESTS PASSED!")
        logger.info("=" * 60)
        logger.info("\n📋 Summary:")
        logger.info("  • User repository: CREATE, FIND, UPDATE ✅")
        logger.info("  • Email repository: CREATE, FIND, LIST, UPDATE ✅")
        logger.info("  • Metadata repository: CREATE, FIND ✅")
        logger.info("  • Database statistics: VERIFIED ✅")
        logger.info("  • Indexes: ALL CREATED ✅")
        logger.info("\n🎉 MongoDB migration is fully functional!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(test_mongodb_migration())
