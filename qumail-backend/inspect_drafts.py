import asyncio
from pprint import pprint

from app.mongo_database import connect_to_mongo, get_database, close_mongo_connection

async def main():
    await connect_to_mongo()
    db = get_database()
    drafts = await db.drafts.find({}).to_list(length=None)
    print(f"Total drafts: {len(drafts)}")
    for draft in drafts:
        print("-" * 40)
        pprint({
            "_id": draft.get("_id"),
            "user_id": draft.get("user_id"),
            "user_email": draft.get("user_email"),
            "recipient": draft.get("recipient"),
            "subject": draft.get("subject"),
            "updated_at": draft.get("updated_at"),
        })
    await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(main())
