"""Check most recent emails in MongoDB"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()

async def check_recent():
    client = AsyncIOMotorClient(os.getenv('DATABASE_URL'))
    db = client.qumail
    
    # Get 5 most recent emails
    print('=' * 70)
    print('5 MOST RECENT EMAILS IN MONGODB')
    print('=' * 70)
    
    cursor = db.emails.find().sort('created_at', -1).limit(5)
    emails = await cursor.to_list(length=5)
    
    for i, email in enumerate(emails, 1):
        subject = email.get('subject', 'N/A')
        flow_id = email.get('flow_id', 'N/A')
        level = email.get('security_level', 'N/A')
        created = email.get('created_at', 'N/A')
        direction = email.get('direction', 'N/A')
        
        print(f'\n[{i}] Subject: {subject}')
        print(f'    Flow ID: {flow_id}')
        print(f'    Security Level: {level}')
        print(f'    Created: {created}')
        print(f'    Direction: {direction}')
        
        meta = email.get('encryption_metadata', {})
        if level == 4:
            pk = meta.get('public_key')
            print(f'    public_key: {len(pk) if pk else "NOT FOUND"} chars')
        elif level == 3:
            kem = meta.get('kem_public_key')
            dsa = meta.get('dsa_public_key')
            print(f'    kem_public_key: {len(kem) if kem else "NOT FOUND"} chars')
            print(f'    dsa_public_key: {len(dsa) if dsa else "NOT FOUND"} chars')
        else:
            print(f'    (Level 1/2 - uses quantum keys, no public keys)')
    
    print('\n' + '=' * 70)
    print('TOTAL COUNTS BY SECURITY LEVEL')
    print('=' * 70)
    for level in [1, 2, 3, 4]:
        count = await db.emails.count_documents({'security_level': level})
        print(f'  Level {level}: {count} emails')
    
    total = await db.emails.count_documents({})
    print(f'\n  TOTAL: {total} emails')
    
    client.close()

if __name__ == '__main__':
    asyncio.run(check_recent())
