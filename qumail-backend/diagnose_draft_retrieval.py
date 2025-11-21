"""Diagnose draft retrieval issues - check what's actually in MongoDB."""
import asyncio
import sys
from app.mongo_database import connect_to_mongo, close_mongo_connection, get_database
from app.mongo_repositories import DraftRepository, UserRepository
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

async def diagnose_drafts():
    """Check drafts in database and compare with what API returns."""
    try:
        logger.info("="*80)
        logger.info("DRAFT RETRIEVAL DIAGNOSTIC")
        logger.info("="*80)
        
        # Connect
        await connect_to_mongo()
        db = get_database()
        draft_repo = DraftRepository(db)
        user_repo = UserRepository(db)
        
        # 1. Check total drafts
        logger.info("\n[1] Checking total drafts in database...")
        total_drafts = await db.drafts.count_documents({})
        logger.info(f"✅ Total drafts in collection: {total_drafts}")
        
        if total_drafts == 0:
            logger.error("❌ No drafts found in database!")
            logger.info("\nPossible reasons:")
            logger.info("  - Drafts are not being saved (check save endpoint logs)")
            logger.info("  - Wrong database connection (check if using fallback)")
            logger.info("  - Drafts in different collection")
            return
        
        # 2. Get all drafts (raw)
        logger.info("\n[2] Fetching all drafts (raw documents)...")
        all_drafts = await db.drafts.find().to_list(length=None)
        logger.info(f"✅ Retrieved {len(all_drafts)} draft documents")
        
        # 3. Show draft structure
        logger.info("\n[3] Analyzing draft structure...")
        for i, draft in enumerate(all_drafts[:3], 1):  # Show first 3
            logger.info(f"\n   Draft {i}:")
            logger.info(f"      _id: {draft.get('_id')}")
            logger.info(f"      user_id: {draft.get('user_id')}")
            logger.info(f"      user_email: {draft.get('user_email')}")
            logger.info(f"      subject: {draft.get('subject', '(empty)')}")
            logger.info(f"      body: {draft.get('body', '(empty)')[:50]}...")
            logger.info(f"      recipient: {draft.get('recipient', '(empty)')}")
            logger.info(f"      created_at: {draft.get('created_at')}")
        
        # 4. Group by user_email
        logger.info("\n[4] Grouping drafts by user_email...")
        user_emails = set(d.get('user_email') for d in all_drafts if d.get('user_email'))
        logger.info(f"✅ Found {len(user_emails)} unique user emails:")
        for email in sorted(user_emails):
            count = sum(1 for d in all_drafts if d.get('user_email') == email)
            logger.info(f"      {email}: {count} draft(s)")
        
        # 5. Check specific user (sarswatomkar8625@gmail.com)
        logger.info("\n[5] Checking drafts for sarswatomkar8625@gmail.com...")
        target_email = "sarswatomkar8625@gmail.com"
        
        # Query directly
        direct_query = await db.drafts.find({"user_email": target_email}).to_list(length=None)
        logger.info(f"✅ Direct query result: {len(direct_query)} draft(s)")
        
        # Query via repository
        repo_query = await draft_repo.list_by_email(target_email)
        logger.info(f"✅ Repository query result: {len(repo_query)} draft(s)")
        
        if len(direct_query) != len(repo_query):
            logger.error(f"❌ MISMATCH! Direct query: {len(direct_query)}, Repository: {len(repo_query)}")
        
        # 6. Check if user exists
        logger.info("\n[6] Checking if user exists in users collection...")
        user = await user_repo.find_by_email(target_email)
        if user:
            logger.info(f"✅ User found:")
            logger.info(f"      ID: {user.id}")
            logger.info(f"      Email: {user.email}")
            logger.info(f"      Display Name: {user.display_name}")
        else:
            logger.error(f"❌ User NOT found in users collection!")
        
        # 7. Check authentication token
        logger.info("\n[7] Checking user authentication status...")
        if user:
            has_token = bool(user.oauth_access_token)
            logger.info(f"   Has access token: {has_token}")
            if not has_token:
                logger.warning("   ⚠️ User may not be properly authenticated")
        
        # 8. Test repository method with all users
        logger.info("\n[8] Testing repository query for all user emails...")
        for email in sorted(user_emails):
            drafts = await draft_repo.list_by_email(email)
            logger.info(f"   {email}: {len(drafts)} draft(s)")
        
        # 9. Check for empty fields
        logger.info("\n[9] Checking for drafts with empty user_email...")
        empty_email_count = await db.drafts.count_documents({
            "$or": [
                {"user_email": None},
                {"user_email": ""},
                {"user_email": {"$exists": False}}
            ]
        })
        if empty_email_count > 0:
            logger.warning(f"   ⚠️ Found {empty_email_count} draft(s) with empty/missing user_email")
        else:
            logger.info(f"   ✅ All drafts have user_email")
        
        # 10. Final summary
        logger.info("\n" + "="*80)
        logger.info("DIAGNOSTIC SUMMARY")
        logger.info("="*80)
        logger.info(f"Total drafts in database: {total_drafts}")
        logger.info(f"Unique users with drafts: {len(user_emails)}")
        logger.info(f"Drafts for sarswatomkar8625@gmail.com: {len(direct_query)}")
        logger.info(f"User authentication status: {'OK' if user and user.oauth_access_token else 'MISSING'}")
        
        if len(direct_query) > 0:
            logger.info("\n✅ DRAFTS EXIST IN DATABASE!")
            logger.info("If frontend shows 'No drafts', check:")
            logger.info("  1. Frontend is calling GET /api/v1/emails/drafts")
            logger.info("  2. Current user email matches: sarswatomkar8625@gmail.com")
            logger.info("  3. Authentication token is valid")
            logger.info("  4. Frontend console shows received data")
            logger.info("  5. Backend logs show 📨 and 📋 emoji messages")
        else:
            logger.error("\n❌ NO DRAFTS FOUND for sarswatomkar8625@gmail.com!")
            logger.info("Possible causes:")
            logger.info("  1. Drafts saved with different user_email")
            logger.info("  2. Drafts not being saved properly")
            logger.info("  3. Database connection issue")
        
    except Exception as e:
        logger.error(f"\n❌ DIAGNOSTIC FAILED: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(diagnose_drafts())
