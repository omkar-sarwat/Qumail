"""Test script to check drafts in MongoDB"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def check_drafts():
    # Connect to MongoDB
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["qumail_db"]
    
    # Get all drafts
    drafts = await db.drafts.find({}).to_list(length=None)
    
    print(f"\n=== Total drafts in database: {len(drafts)} ===\n")
    
    for draft in drafts:
        print(f"Draft ID: {draft.get('_id')}")
        print(f"User Email: {draft.get('user_email')}")
        print(f"User ID: {draft.get('user_id')}")
        print(f"Subject: {draft.get('subject')}")
        print(f"To: {draft.get('recipient')}")
        print(f"Created: {draft.get('created_at')}")
        print("-" * 50)
    
    # Get all users to compare emails
    users = await db.users.find({}).to_list(length=None)
    print(f"\n=== Total users in database: {len(users)} ===\n")
    
    for user in users:
        print(f"User ID: {user.get('_id')}")
        print(f"Email: {user.get('email')}")
        print(f"Name: {user.get('name', 'N/A')}")
        print("-" * 50)
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_drafts())
