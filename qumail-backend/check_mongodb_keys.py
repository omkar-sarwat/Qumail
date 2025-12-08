"""Query MongoDB to show public keys stored in emails collection."""
import asyncio
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()
MONGODB_URI = os.getenv("DATABASE_URL", "mongodb+srv://user:password@cluster.mongodb.net/qumail?retryWrites=true&w=majority")

async def check_mongodb_public_keys():
    print("=" * 70)
    print("Checking MongoDB for Public Keys in Emails Collection")
    print("=" * 70)
    
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client.qumail
    
    # Find emails with security level 3 or 4
    cursor = db.emails.find(
        {"security_level": {"$in": [3, 4]}},
        {"flow_id": 1, "security_level": 1, "rsa_public_key": 1, "kem_public_key": 1, 
         "dsa_public_key": 1, "private_key_ref": 1, "encryption_metadata": 1, "created_at": 1}
    ).sort("created_at", -1).limit(10)
    
    emails = await cursor.to_list(length=10)
    
    if not emails:
        print("\n⚠️  No Level 3 or Level 4 encrypted emails found in MongoDB yet.")
        print("   Send an encrypted email first to see the public keys stored.")
    else:
        print(f"\nFound {len(emails)} Level 3/4 encrypted email(s):\n")
        
        for i, email in enumerate(emails, 1):
            level = email.get("security_level")
            flow_id = email.get("flow_id", "N/A")
            
            print(f"[{i}] Flow ID: {flow_id}")
            print(f"    Security Level: {level}")
            print(f"    private_key_ref: {email.get('private_key_ref', 'NOT SET')}")
            
            if level == 4:
                rsa_pk = email.get("rsa_public_key")
                if rsa_pk:
                    print(f"    ✅ rsa_public_key: {len(rsa_pk)} chars")
                else:
                    # Check in encryption_metadata
                    meta = email.get("encryption_metadata", {})
                    rsa_pk_meta = meta.get("public_key")
                    if rsa_pk_meta:
                        print(f"    ✅ public_key (in metadata): {len(rsa_pk_meta)} chars")
                    else:
                        print(f"    ❌ rsa_public_key: MISSING")
                        
            elif level == 3:
                kem_pk = email.get("kem_public_key")
                dsa_pk = email.get("dsa_public_key")
                meta = email.get("encryption_metadata", {})
                
                if kem_pk:
                    print(f"    ✅ kem_public_key: {len(kem_pk)} chars")
                elif meta.get("kem_public_key"):
                    print(f"    ✅ kem_public_key (in metadata): {len(meta['kem_public_key'])} chars")
                else:
                    print(f"    ❌ kem_public_key: MISSING")
                    
                if dsa_pk:
                    print(f"    ✅ dsa_public_key: {len(dsa_pk)} chars")
                elif meta.get("dsa_public_key"):
                    print(f"    ✅ dsa_public_key (in metadata): {len(meta['dsa_public_key'])} chars")
                else:
                    print(f"    ❌ dsa_public_key: MISSING")
            
            print()
    
    # Also show collection stats
    total_emails = await db.emails.count_documents({})
    level3_count = await db.emails.count_documents({"security_level": 3})
    level4_count = await db.emails.count_documents({"security_level": 4})
    
    print("-" * 70)
    print(f"Collection Stats:")
    print(f"  Total emails: {total_emails}")
    print(f"  Level 3 (PQC) emails: {level3_count}")
    print(f"  Level 4 (RSA) emails: {level4_count}")
    print("=" * 70)
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_mongodb_public_keys())
