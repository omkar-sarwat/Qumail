#!/usr/bin/env python3
"""Check quantum emails in database and their Gmail message IDs"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine, text
import json

# Database connection - use aiomysql
DATABASE_URL = "mysql+aiomysql://root:Omkar%40123@localhost:3306/qumail_db"
engine = create_engine(DATABASE_URL, echo=False)

print("\n" + "="*100)
print("CHECKING QUANTUM EMAILS IN DATABASE")
print("="*100 + "\n")

with engine.connect() as conn:
    # Get all emails ordered by most recent
    result = conn.execute(text("""
        SELECT 
            id,
            gmail_message_id,
            flow_id,
            subject,
            security_level,
            sender_email,
            receiver_email,
            LENGTH(body_encrypted) as encrypted_length,
            encryption_metadata,
            timestamp,
            direction
        FROM emails
        WHERE security_level > 0
        ORDER BY timestamp DESC
        LIMIT 10
    """))
    
    emails = result.fetchall()
    
    if not emails:
        print("❌ NO QUANTUM EMAILS FOUND IN DATABASE!")
        print("\nThis means:")
        print("1. No quantum emails have been sent through QuMail")
        print("2. The emails you see in Gmail are NOT in QuMail's database")
        print("3. You need to send a quantum email through QuMail first\n")
    else:
        print(f"✅ Found {len(emails)} quantum emails:\n")
        
        for email in emails:
            print("-"*100)
            print(f"Email ID: {email[0]}")
            print(f"Gmail Message ID: {email[1] or 'NOT SET'}")
            print(f"Flow ID: {email[2]}")
            print(f"Subject: {email[3]}")
            print(f"Security Level: {email[4]}")
            print(f"Sender: {email[5]}")
            print(f"Receiver: {email[6]}")
            print(f"Encrypted Body Length: {email[7]} bytes")
            print(f"Direction: {email[10]}")
            
            # Parse metadata
            metadata_raw = email[8]
            if metadata_raw:
                try:
                    if isinstance(metadata_raw, str):
                        metadata = json.loads(metadata_raw)
                    else:
                        metadata = metadata_raw
                    
                    print(f"\nEncryption Metadata:")
                    print(f"  Algorithm: {metadata.get('algorithm', 'Not set')}")
                    print(f"  Quantum Enhanced: {metadata.get('quantum_enhanced', 'Not set')}")
                    print(f"  Key ID: {metadata.get('key_id', 'Not set')}")
                    print(f"  Encrypted Size: {metadata.get('encrypted_size', 'Not set')}")
                except:
                    print(f"\nEncryption Metadata: {metadata_raw}")
            else:
                print(f"\nEncryption Metadata: None")
            
            print(f"Timestamp: {email[9]}")
            print()
        
        print("="*100)
        print("\nNOW CHECK IF THESE GMAIL MESSAGE IDs MATCH YOUR GMAIL INBOX:")
        print("-"*100)
        for email in emails:
            if email[1]:  # Has gmail_message_id
                print(f"✓ Subject: {email[3]}")
                print(f"  Gmail ID: {email[1]}")
                print(f"  When you click this email in Gmail folder, backend should find it")
                print()
            else:
                print(f"✗ Subject: {email[3]}")
                print(f"  Gmail ID: NOT SET - This email was NOT sent via Gmail API")
                print(f"  This won't show in Gmail folders")
                print()

print("\n" + "="*100)
print("NEXT STEPS:")
print("="*100)
print("1. If no emails found: Send a quantum email through QuMail's compose")
print("2. If emails found but no gmail_message_id: Check Gmail API integration")
print("3. If gmail_message_id exists: Check if it matches the email in Gmail")
print("4. Backend should log when you click the email: '🔍 Looking for quantum record'")
print("="*100 + "\n")
