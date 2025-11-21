"""Script to initialize MongoDB collections and indexes on MongoDB Atlas."""
import asyncio
import sys
from app.mongo_database import connect_to_mongo, close_mongo_connection, init_collections, get_database
from app.mongo_repositories import UserRepository, EmailRepository
from app.mongo_models import UserDocument
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def push_database():
    """Initialize MongoDB collections and test connection."""
    try:
        # Connect to MongoDB Atlas
        logger.info("Connecting to MongoDB Atlas...")
        await connect_to_mongo()
        logger.info("✅ Connected to MongoDB Atlas successfully!")
        
        # Initialize collections with indexes
        logger.info("Creating collections and indexes...")
        await init_collections()
        logger.info("✅ Collections and indexes created successfully!")
        
        # Get database instance
        db = get_database()
        
        # Test: List all collections
        collections = await db.list_collection_names()
        logger.info(f"✅ Available collections: {collections}")
        
        # Test: Create a test user
        logger.info("Testing user creation...")
        user_repo = UserRepository(db)
        
        # Check if test user exists
        test_user = await user_repo.find_by_email("test@qumail.com")
        if not test_user:
            test_user_doc = UserDocument(
                email="test@qumail.com",
                display_name="Test User",
                last_login=datetime.utcnow()
            )
            test_user = await user_repo.create(test_user_doc)
            logger.info(f"✅ Created test user: {test_user.email} (ID: {test_user.id})")
        else:
            logger.info(f"✅ Test user already exists: {test_user.email} (ID: {test_user.id})")
        
        # Test: Count documents
        user_count = await db.users.count_documents({})
        email_count = await db.emails.count_documents({})
        logger.info(f"✅ Database stats: {user_count} users, {email_count} emails")
        
        # Test: List indexes
        logger.info("Indexes created:")
        for collection_name in collections:
            indexes = await db[collection_name].index_information()
            logger.info(f"  {collection_name}: {list(indexes.keys())}")
        
        logger.info("\n" + "="*60)
        logger.info("✅ MongoDB Atlas database initialization complete!")
        logger.info("✅ All collections, indexes, and tests passed successfully!")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await close_mongo_connection()
        logger.info("Connection closed.")

if __name__ == "__main__":
    asyncio.run(push_database())
