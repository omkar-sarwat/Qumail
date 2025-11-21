"""Clear all emails from database for fresh testing"""
import asyncio
from app.database import get_db
from app.models.email import Email
from sqlalchemy import delete

async def clear_emails():
    async for db in get_db():
        result = await db.execute(delete(Email))
        await db.commit()
        print(f'✅ Deleted {result.rowcount} emails from database')
        print('Database is now clean for fresh testing')
        break

if __name__ == "__main__":
    asyncio.run(clear_emails())
