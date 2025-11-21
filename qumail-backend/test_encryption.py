import asyncio
import json
import base64
from app.services.encryption.level1_otp import encrypt_otp, decrypt_otp
from app.services.encryption.level2_aes import encrypt_aes, decrypt_aes
from app.services.encryption.level3_pqc import encrypt_pqc, decrypt_pqc, is_pqc_available
from app.services.encryption.level4_rsa import encrypt_rsa_hybrid, decrypt_rsa_hybrid

async def test_all_encryption_levels():
    """
    Test all four security levels of the quantum encryption system
    """
    # Test data
    test_content = "This is a highly confidential message protected by quantum encryption!"
    test_email = "quantum.user@example.com"
    
    print("\n🔐 QUMAIL SECURE EMAIL ENCRYPTION TEST 🔐\n")
    
    # ========== LEVEL 1: Quantum One-Time Pad ==========
    print("\n📋 TESTING LEVEL 1: QUANTUM ONE-TIME PAD")
    print("------------------------------------------")
    print("Description: Perfect secrecy using quantum keys")
    
    try:
        print("Encrypting with Level 1 OTP...")
        level1_result = await encrypt_otp(test_content, test_email)
        
        print(f"✅ Encryption successful")
        print(f"Algorithm: {level1_result.get('algorithm', 'One-Time Pad')}")
        print(f"Security level: {level1_result['metadata']['security_level']}")
        print(f"Flow ID: {level1_result['metadata']['flow_id']}")
        
        print("\nDecrypting with Level 1 OTP...")
        level1_decrypted = await decrypt_otp(
            level1_result['encrypted_content'],
            test_email,
            level1_result['metadata']
        )
        
        if level1_decrypted['decrypted_content'] == test_content:
            print(f"✅ Decryption successful! Content matches original.")
        else:
            print(f"❌ Decryption failed! Content doesn't match.")
    except Exception as e:
        print(f"❌ Level 1 test failed: {e}")
    
    # ========== LEVEL 2: Quantum-Enhanced AES ==========
    print("\n📋 TESTING LEVEL 2: QUANTUM-ENHANCED AES")
    print("------------------------------------------")
    print("Description: AES-256-GCM with quantum keys")
    
    try:
        print("Encrypting with Level 2 Quantum-Enhanced AES...")
        level2_result = await encrypt_aes(test_content, test_email)
        
        print(f"✅ Encryption successful")
        print(f"Algorithm: {level2_result.get('algorithm', 'AES-256-GCM')}")
        print(f"Security level: {level2_result['metadata']['security_level']}")
        print(f"Flow ID: {level2_result['metadata']['flow_id']}")
        
        print("\nDecrypting with Level 2 Quantum-Enhanced AES...")
        level2_decrypted = await decrypt_aes(
            level2_result['encrypted_content'],
            test_email,
            level2_result['metadata']
        )
        
        if level2_decrypted['decrypted_content'] == test_content:
            print(f"✅ Decryption successful! Content matches original.")
        else:
            print(f"❌ Decryption failed! Content doesn't match.")
    except Exception as e:
        print(f"❌ Level 2 test failed: {e}")
    
    # ========== LEVEL 3: Post-Quantum Cryptography ==========
    print("\n📋 TESTING LEVEL 3: POST-QUANTUM CRYPTOGRAPHY")
    print("------------------------------------------")
    print(f"Description: Kyber1024 & Dilithium5 PQC (Available: {is_pqc_available()})")
    
    try:
        print("Encrypting with Level 3 Post-Quantum Cryptography...")
        level3_result = await encrypt_pqc(test_content, test_email)
        
        print(f"✅ Encryption successful")
        print(f"Algorithm: {level3_result.get('algorithm', 'Kyber1024+Dilithium5')}")
        print(f"Security level: {level3_result['metadata']['security_level']}")
        print(f"Flow ID: {level3_result['metadata']['flow_id']}")
        
        print("\nDecrypting with Level 3 Post-Quantum Cryptography...")
        level3_decrypted = await decrypt_pqc(
            level3_result['encrypted_content'],
            test_email,
            level3_result['metadata']
        )
        
        if level3_decrypted['decrypted_content'] == test_content:
            print(f"✅ Decryption successful! Content matches original.")
        else:
            print(f"❌ Decryption failed! Content doesn't match.")
    except Exception as e:
        print(f"❌ Level 3 test failed: {e}")
    
    # ========== LEVEL 4: RSA Hybrid ==========
    print("\n📋 TESTING LEVEL 4: RSA HYBRID")
    print("------------------------------------------")
    print("Description: RSA-4096 with AES-256-GCM")
    
    try:
        print("Encrypting with Level 4 RSA Hybrid...")
        level4_result = await encrypt_rsa_hybrid(test_content, test_email)
        
        print(f"✅ Encryption successful")
        print(f"Algorithm: {level4_result.get('algorithm', 'RSA-4096-Hybrid')}")
        print(f"Security level: {level4_result['metadata']['security_level']}")
        print(f"Flow ID: {level4_result['metadata']['flow_id']}")
        
        print("\nDecrypting with Level 4 RSA Hybrid...")
        level4_decrypted = await decrypt_rsa_hybrid(
            level4_result['encrypted_content'],
            test_email,
            level4_result['metadata']
        )
        
        if level4_decrypted['decrypted_content'] == test_content:
            print(f"✅ Decryption successful! Content matches original.")
        else:
            print(f"❌ Decryption failed! Content doesn't match.")
    except Exception as e:
        print(f"❌ Level 4 test failed: {e}")
    
    print("\n🔍 ENCRYPTION TEST SUMMARY")
    print("==========================")
    successes = []
    
    try:
        if level1_decrypted['decrypted_content'] == test_content:
            successes.append("Level 1: One-Time Pad")
    except:
        pass
        
    try:
        if level2_decrypted['decrypted_content'] == test_content:
            successes.append("Level 2: Quantum-Enhanced AES")
    except:
        pass
        
    try:
        if level3_decrypted['decrypted_content'] == test_content:
            successes.append("Level 3: Post-Quantum Cryptography")
    except:
        pass
        
    try:
        if level4_decrypted['decrypted_content'] == test_content:
            successes.append("Level 4: RSA Hybrid")
    except:
        pass
    
    print(f"Successfully tested {len(successes)} out of 4 security levels:")
    for success in successes:
        print(f"✅ {success}")
    
    if len(successes) < 4:
        print("\nFailed security levels:")
        if "Level 1: One-Time Pad" not in successes:
            print("❌ Level 1: One-Time Pad")
        if "Level 2: Quantum-Enhanced AES" not in successes:
            print("❌ Level 2: Quantum-Enhanced AES")
        if "Level 3: Post-Quantum Cryptography" not in successes:
            print("❌ Level 3: Post-Quantum Cryptography")
        if "Level 4: RSA Hybrid" not in successes:
            print("❌ Level 4: RSA Hybrid")

if __name__ == "__main__":
    asyncio.run(test_all_encryption_levels())