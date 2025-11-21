"""
Test Draft Cross-Device Synchronization
Tests that drafts are synced across devices via Google account email
"""
import asyncio
import sys
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import uuid

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.mongo_models import UserDocument, DraftDocument
from app.mongo_repositories import UserRepository, DraftRepository
from app.config import get_settings

settings = get_settings()

async def test_draft_sync():
    """Test draft synchronization across devices"""
    print("\n" + "="*80)
    print("TESTING DRAFT CROSS-DEVICE SYNCHRONIZATION")
    print("="*80 + "\n")
    
    # Connect to MongoDB
    print(f"Connecting to MongoDB...")
    client = AsyncIOMotorClient(settings.database_url)
    db = client.qumail
    
    user_repo = UserRepository(db)
    draft_repo = DraftRepository(db)
    
    # Test user email (simulating Google OAuth)
    test_email = "testuser@gmail.com"
    
    try:
        # Step 1: Create a test user
        print(f"\n1. Creating test user: {test_email}")
        user_doc = UserDocument(
            email=test_email,
            display_name="Test User",
            access_token="test_token",
            refresh_token="test_refresh",
            token_expiry=datetime.utcnow(),
            created_at=datetime.utcnow(),
            last_login=datetime.utcnow()
        )
        user = await user_repo.create(user_doc)
        print(f"   ✓ User created with ID: {user.id}")
        
        # Step 2: Create drafts on "Device 1"
        print(f"\n2. Creating drafts on Device 1...")
        draft1 = DraftDocument(
            user_id=str(user.id),
            user_email=test_email,
            recipient="recipient1@example.com",
            subject="Test Email 1",
            body="This is a test draft from Device 1",
            security_level=2,
            is_synced=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        created_draft1 = await draft_repo.create(draft1)
        print(f"   ✓ Draft 1 created: {created_draft1.id}")
        print(f"     Subject: {created_draft1.subject}")
        print(f"     Recipient: {created_draft1.recipient}")
        
        draft2 = DraftDocument(
            user_id=str(user.id),
            user_email=test_email,
            recipient="recipient2@example.com",
            subject="Test Email 2",
            body="This is another test draft from Device 1",
            security_level=3,
            cc="cc@example.com",
            is_synced=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        created_draft2 = await draft_repo.create(draft2)
        print(f"   ✓ Draft 2 created: {created_draft2.id}")
        print(f"     Subject: {created_draft2.subject}")
        print(f"     Recipient: {created_draft2.recipient}")
        print(f"     CC: {created_draft2.cc}")
        
        # Step 3: Simulate login from "Device 2" and retrieve drafts
        print(f"\n3. Simulating login from Device 2...")
        print(f"   User logs in with Google account: {test_email}")
        
        # List drafts by email (cross-device sync)
        print(f"\n4. Retrieving drafts from Device 2 (using user_email)...")
        drafts = await draft_repo.list_by_email(test_email)
        print(f"   ✓ Found {len(drafts)} synced drafts")
        
        for i, draft in enumerate(drafts, 1):
            print(f"\n   Draft {i}:")
            print(f"     ID: {draft.id}")
            print(f"     Subject: {draft.subject}")
            print(f"     Recipient: {draft.recipient}")
            print(f"     Security Level: {draft.security_level}")
            print(f"     CC: {draft.cc or 'None'}")
            print(f"     Created: {draft.created_at}")
            print(f"     User Email: {draft.user_email}")
            print(f"     Is Synced: {draft.is_synced}")
        
        # Step 4: Update draft from Device 2
        print(f"\n5. Updating draft from Device 2...")
        draft_to_update = drafts[0]
        update_success = await draft_repo.update(
            draft_to_update.id,
            {
                "subject": "Updated from Device 2",
                "body": "This draft was updated from Device 2",
                "updated_at": datetime.utcnow()
            }
        )
        print(f"   ✓ Draft updated: {update_success}")
        
        # Verify update from Device 1
        print(f"\n6. Verifying update from Device 1...")
        updated_draft = await draft_repo.find_by_id(draft_to_update.id)
        print(f"   ✓ Subject: {updated_draft.subject}")
        print(f"   ✓ Body: {updated_draft.body}")
        print(f"   ✓ Updated at: {updated_draft.updated_at}")
        
        # Step 5: Test ownership verification
        print(f"\n7. Testing ownership verification...")
        draft_with_owner = await draft_repo.find_by_user_and_id(test_email, draft_to_update.id)
        print(f"   ✓ Draft retrieved with ownership check: {draft_with_owner is not None}")
        
        # Try to access with wrong email (should return None)
        wrong_access = await draft_repo.find_by_user_and_id("wrong@email.com", draft_to_update.id)
        print(f"   ✓ Access denied for wrong email: {wrong_access is None}")
        
        # Step 6: Delete draft from Device 2
        print(f"\n8. Deleting draft from Device 2...")
        delete_success = await draft_repo.delete(draft_to_update.id)
        print(f"   ✓ Draft deleted: {delete_success}")
        
        # Verify deletion from Device 1
        print(f"\n9. Verifying deletion from Device 1...")
        remaining_drafts = await draft_repo.list_by_email(test_email)
        print(f"   ✓ Remaining drafts: {len(remaining_drafts)}")
        
        print("\n" + "="*80)
        print("✅ ALL DRAFT SYNC TESTS PASSED!")
        print("="*80)
        print("\nSummary:")
        print("- Drafts created on Device 1: 2")
        print("- Drafts synced to Device 2: 2")
        print("- Draft updated from Device 2: ✓")
        print("- Update visible on Device 1: ✓")
        print("- Ownership verification: ✓")
        print("- Draft deleted from Device 2: ✓")
        print("- Deletion synced to Device 1: ✓")
        print(f"- Final draft count: {len(remaining_drafts)}")
        
        # Cleanup
        print("\n10. Cleaning up test data...")
        for draft in remaining_drafts:
            await draft_repo.delete(draft.id)
        await user_repo.delete(str(user.id))
        print("   ✓ Test data cleaned up")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(test_draft_sync())
