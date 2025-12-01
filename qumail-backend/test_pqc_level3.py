"""
Test script for Level 3 PQC encryption using pqcrypto library
"""
import asyncio
import sys
sys.path.insert(0, '.')

async def test_level3_pqc():
    try:
        from app.services.encryption.level3_pqc import (
            encrypt_pqc, decrypt_pqc, is_pqc_available, 
            PQC_AVAILABLE, MLKEM, MLDSA
        )
        
        print("=" * 60)
        print("Level 3 PQC Test - Using PQCrypto Library")
        print("=" * 60)
        
        print(f"\nPQC Available: {is_pqc_available()}")
        print(f"PQC_AVAILABLE flag: {PQC_AVAILABLE}")
        
        # Test ML-KEM-1024 key generation
        print("\n--- Testing ML-KEM-1024 (Kyber) ---")
        sk, pk = MLKEM.generate_keypair()
        print(f"Secret key size: {len(sk)} bytes")
        print(f"Public key size: {len(pk)} bytes")
        
        # Test ML-DSA-87 key generation
        print("\n--- Testing ML-DSA-87 (Dilithium) ---")
        dsk, dpk = MLDSA.generate_keypair()
        print(f"Secret key size: {len(dsk)} bytes")
        print(f"Public key size: {len(dpk)} bytes")
        
        # Test full encryption/decryption
        print("\n--- Testing Full Encryption/Decryption ---")
        test_message = "Hello, this is a secret quantum-safe message!"
        print(f"Original message: {test_message}")
        
        result = await encrypt_pqc(test_message, "test@example.com")
        print(f"\nEncryption successful!")
        print(f"  Algorithm: {result['algorithm']}")
        print(f"  PQC Library: {result['metadata']['pqc_library']}")
        print(f"  PQC Algorithms: {result['metadata']['pqc_algorithms']}")
        
        # Test decryption
        decrypted = await decrypt_pqc(
            result['encrypted_content'], 
            "test@example.com", 
            result['metadata']
        )
        print(f"\nDecryption successful!")
        print(f"  Decrypted: {decrypted['decrypted_content']}")
        print(f"  Verification: {decrypted['verification_status']}")
        print(f"  Algorithm: {decrypted['metadata']['algorithm']}")
        
        if decrypted['decrypted_content'] == test_message:
            print("\n" + "=" * 60)
            print("✅ Level 3 PQC TEST PASSED - pqcrypto working correctly!")
            print("=" * 60)
            return True
        else:
            print("\n❌ TEST FAILED - messages don't match")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_level3_pqc())
    sys.exit(0 if success else 1)
