import asyncio
import os
from app.database import engine, init_db
from sqlalchemy import text

async def recreate_database():
    print('Dropping existing tables...')
    async with engine.begin() as conn:
        # Drop all tables
        await conn.execute(text('DROP TABLE IF EXISTS key_usage'))
        await conn.execute(text('DROP TABLE IF EXISTS users'))
        await conn.commit()
    
    print('Recreating database schema with all columns...')
    await init_db()
    print('Database recreated successfully!')

if __name__ == "__main__":
    asyncio.run(recreate_database())