#!/usr/bin/env python3
"""Check email metadata in database"""
import asyncio
import json
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text
from app.models.email import Email

async def check_email_metadata():
    """Check email metadata for the most recent email"""
    # Create async engine
    DATABASE_URL = "mysql+aiomysql://root:Omkar%40123@localhost:3306/qumail_db"
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Get the most recent email
        result = await session.execute(
            select(Email).order_by(Email.timestamp.desc()).limit(5)
        )
        emails = result.scalars().all()
        
        if not emails:
            print("❌ No emails found in database")
            return
        
        print(f"\n📧 Found {len(emails)} most recent emails:\n")
        print("="*100)
        
        for email in emails:
            print(f"\nEmail ID: {email.id}")
            print(f"Gmail Message ID: {email.gmail_message_id}")
            print(f"Flow ID: {email.flow_id}")
            print(f"Subject: {email.subject}")
            print(f"Security Level: {email.security_level}")
            print(f"Sender: {email.sender_email}")
            print(f"Receiver: {email.receiver_email}")
            print(f"Timestamp: {email.timestamp}")
            print(f"Body Encrypted Length: {len(email.body_encrypted or '')}")
            
            print(f"\n📋 Encryption Metadata:")
            if email.encryption_metadata:
                if isinstance(email.encryption_metadata, str):
                    try:
                        metadata_dict = json.loads(email.encryption_metadata)
                        print(json.dumps(metadata_dict, indent=2))
                    except json.JSONDecodeError:
                        print(f"  Raw string: {email.encryption_metadata}")
                else:
                    print(json.dumps(email.encryption_metadata, indent=2))
            else:
                print("  None")
            
            print("-"*100)
        
        print("\n✅ Database check complete\n")

if __name__ == "__main__":
    asyncio.run(check_email_metadata())
