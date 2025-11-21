"""View MongoDB Atlas data."""
import asyncio
from app.mongo_database import connect_to_mongo, close_mongo_connection, get_database
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def view_mongodb_data():
    """View all data in MongoDB Atlas."""
    try:
        await connect_to_mongo()
        db = get_database()
        
        logger.info("\n" + "="*70)
        logger.info("MONGODB ATLAS DATA VIEWER")
        logger.info("="*70)
        
        # Get all collections
        collections = await db.list_collection_names()
        
        for collection_name in collections:
            collection = db[collection_name]
            count = await collection.count_documents({})
            
            logger.info(f"\n📂 Collection: {collection_name}")
            logger.info(f"   Total documents: {count}")
            
            if count > 0 and count <= 10:  # Only show data if 10 or fewer documents
                logger.info("   Documents:")
                cursor = collection.find().limit(10)
                docs = await cursor.to_list(length=10)
                for i, doc in enumerate(docs, 1):
                    # Remove _id for cleaner output, but show custom id
                    doc_id = doc.get('_id', 'N/A')
                    logger.info(f"   [{i}] ID: {doc_id}")
                    for key, value in doc.items():
                        if key != '_id':
                            # Truncate long values
                            str_value = str(value)
                            if len(str_value) > 80:
                                str_value = str_value[:77] + "..."
                            logger.info(f"       {key}: {str_value}")
            elif count > 10:
                logger.info(f"   (Showing first 3 of {count} documents)")
                cursor = collection.find().limit(3)
                docs = await cursor.to_list(length=3)
                for i, doc in enumerate(docs, 1):
                    doc_id = doc.get('_id', 'N/A')
                    email = doc.get('email', doc.get('flow_id', 'N/A'))
                    logger.info(f"   [{i}] ID: {doc_id} | Key field: {email}")
        
        logger.info("\n" + "="*70)
        logger.info("✅ MongoDB Atlas data view complete!")
        logger.info("="*70)
        
    except Exception as e:
        logger.error(f"❌ Error viewing data: {e}")
    finally:
        await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(view_mongodb_data())
