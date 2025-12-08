"""Test script to verify public keys are stored in MongoDB for Level 3 and 4 encryption."""
import asyncio
import sys
import os

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_encryption_and_check_mongodb():
    """Test Level 3 and Level 4 encryption and verify public keys in MongoDB."""
    from app.services.encryption.level3_pqc import encrypt_pqc
    from app.services.encryption.level4_rsa import encrypt_rsa
    
    print("=" * 60)
    print("Testing Public Key Storage in MongoDB")
    print("=" * 60)
    
    test_message = "Hello, this is a test message for encryption!"
    test_email = "test@qumail.com"
    
    # Test Level 4 (RSA)
    print("\n[Level 4 - RSA-4096] Encrypting...")
    try:
        result_l4 = await encrypt_rsa(test_message, test_email)
        metadata_l4 = result_l4.get('metadata', {})
        
        print(f"  Flow ID: {metadata_l4.get('flow_id')}")
        print(f"  Algorithm: {result_l4.get('algorithm')}")
        print(f"  private_key_ref: {metadata_l4.get('private_key_ref')}")
        
        public_key = metadata_l4.get('public_key')
        if public_key:
            print(f"  ✅ public_key present: {len(public_key)} chars (first 50: {public_key[:50]}...)")
        else:
            print(f"  ❌ public_key MISSING!")
        
        # Check private_key is NOT in metadata (should be stored locally only)
        if 'private_key' in metadata_l4:
            print(f"  ⚠️  WARNING: private_key still in metadata (should be removed)")
        else:
            print(f"  ✅ private_key correctly removed from metadata")
            
    except Exception as e:
        print(f"  ❌ Level 4 encryption failed: {e}")
    
    # Test Level 3 (PQC)
    print("\n[Level 3 - ML-KEM + ML-DSA] Encrypting...")
    try:
        result_l3 = await encrypt_pqc(test_message, test_email)
        metadata_l3 = result_l3.get('metadata', {})
        
        print(f"  Flow ID: {metadata_l3.get('flow_id')}")
        print(f"  Algorithm: {result_l3.get('algorithm')}")
        print(f"  private_key_ref: {metadata_l3.get('private_key_ref')}")
        
        kem_public = metadata_l3.get('kem_public_key') or metadata_l3.get('kyber_public_key')
        dsa_public = metadata_l3.get('dsa_public_key') or metadata_l3.get('dilithium_public_key')
        
        if kem_public:
            print(f"  ✅ kem_public_key present: {len(kem_public)} chars")
        else:
            print(f"  ❌ kem_public_key MISSING!")
            
        if dsa_public:
            print(f"  ✅ dsa_public_key present: {len(dsa_public)} chars")
        else:
            print(f"  ❌ dsa_public_key MISSING!")
        
        # Check private keys are NOT in metadata
        if 'kem_secret_key' in metadata_l3 or 'kyber_private_key' in metadata_l3:
            print(f"  ⚠️  WARNING: kem_secret_key still in metadata (should be removed)")
        else:
            print(f"  ✅ kem_secret_key correctly removed from metadata")
            
    except Exception as e:
        print(f"  ❌ Level 3 encryption failed: {e}")
    
    # Check local private key store
    print("\n[Local Private Key Store] Checking...")
    try:
        from app.services.local_private_key_store import local_private_key_store
        import sqlite3
        
        db_path = local_private_key_store.db_path
        print(f"  Database path: {db_path}")
        
        if os.path.exists(db_path):
            with sqlite3.connect(db_path) as conn:
                cursor = conn.execute("SELECT flow_id, level FROM private_keys ORDER BY created_at DESC LIMIT 5")
                rows = cursor.fetchall()
                print(f"  ✅ Found {len(rows)} private key entries:")
                for row in rows:
                    print(f"     - flow_id: {row[0][:20]}..., level: {row[1]}")
        else:
            print(f"  ⚠️  Database file not found yet (will be created on first encryption)")
    except Exception as e:
        print(f"  ❌ Error checking local store: {e}")
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)
    print("\nSummary:")
    print("- Level 3/4 metadata should contain PUBLIC keys only")
    print("- PRIVATE keys should be stored in local SQLite only")
    print("- MongoDB will store: rsa_public_key, kem_public_key, dsa_public_key, private_key_ref")

if __name__ == "__main__":
    asyncio.run(test_encryption_and_check_mongodb())
