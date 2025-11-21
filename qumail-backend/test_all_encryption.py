import asyncio
import logging
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Import all encryption levels
try:
    from app.services.encryption.level1_otp import encrypt_otp, decrypt_otp
    from app.services.encryption.level2_aes import encrypt_aes, decrypt_aes
    from app.services.encryption.level3_pqc import encrypt_pqc, decrypt_pqc, is_pqc_available
    from app.services.encryption.level4_rsa import encrypt_rsa, decrypt_rsa
except ImportError as e:
    print(f"Import error: {e}")
    traceback.print_exc()
    exit(1)

async def test_level1_otp():
    """Test Level 1: Quantum One-Time Pad encryption"""
    print("\n=== Testing Level 1: Quantum One-Time Pad ===")
    content = "This is a Level 1 OTP encrypted message!"
    user_email = "user@example.com"
    
    try:
        print("Encrypting with OTP...")
        encrypted_result = await encrypt_otp(content, user_email)
        
        print(f"Encrypted successfully with algorithm: {encrypted_result['algorithm']}")
        print(f"Encrypted content length: {len(encrypted_result['encrypted_content'])}")
        
        print("Decrypting with OTP...")
        decrypted_result = await decrypt_otp(
            encrypted_result['encrypted_content'],
            user_email,
            encrypted_result['metadata']
        )
        
        print(f"Decryption successful: {decrypted_result['decrypted_content'] == content}")
        print(f"Decrypted content: {decrypted_result['decrypted_content']}")
        return True
    except Exception as e:
        print(f"Level 1 OTP test failed: {e}")
        traceback.print_exc()
        return False

async def test_level2_aes():
    """Test Level 2: AES-256-GCM encryption"""
    print("\n=== Testing Level 2: AES-256-GCM ===")
    content = "This is a Level 2 AES encrypted message with authenticated encryption!"
    user_email = "user@example.com"
    
    try:
        print("Encrypting with AES-256-GCM...")
        encrypted_result = await encrypt_aes(content, user_email)
        
        print(f"Encrypted successfully with algorithm: {encrypted_result['algorithm']}")
        print(f"Encrypted content length: {len(encrypted_result['encrypted_content'])}")
        
        print("Decrypting with AES-256-GCM...")
        decrypted_result = await decrypt_aes(
            encrypted_result['encrypted_content'],
            user_email,
            encrypted_result['metadata']
        )
        
        print(f"Decryption successful: {decrypted_result['decrypted_content'] == content}")
        print(f"Decrypted content: {decrypted_result['decrypted_content']}")
        return True
    except Exception as e:
        print(f"Level 2 AES test failed: {e}")
        traceback.print_exc()
        return False

async def test_level3_pqc():
    """Test Level 3: Post-Quantum Cryptography"""
    print("\n=== Testing Level 3: Post-Quantum Cryptography ===")
    content = "This is a Level 3 Post-Quantum encrypted message that's resistant to quantum computers!"
    user_email = "user@example.com"
    
    try:
        print(f"PQC Available: {is_pqc_available()}")
        
        print("Encrypting with PQC...")
        encrypted_result = await encrypt_pqc(content, user_email)
        
        print(f"Encrypted successfully with algorithm: {encrypted_result['algorithm']}")
        print(f"Encrypted content length: {len(encrypted_result['encrypted_content'])}")
        
        print("Decrypting with PQC...")
        decrypted_result = await decrypt_pqc(
            encrypted_result['encrypted_content'],
            user_email,
            encrypted_result['metadata']
        )
        
        print(f"Decryption successful: {decrypted_result['decrypted_content'] == content}")
        print(f"Decrypted content: {decrypted_result['decrypted_content']}")
        return True
    except Exception as e:
        print(f"Level 3 PQC test failed: {e}")
        traceback.print_exc()
        return False

async def test_level4_rsa():
    """Test Level 4: Hybrid RSA+AES encryption"""
    print("\n=== Testing Level 4: Hybrid RSA+AES ===")
    content = "This is a Level 4 RSA+AES hybrid encrypted message for maximum compatibility!"
    user_email = "user@example.com"
    
    try:
        print("Encrypting with RSA+AES...")
        encrypted_result = await encrypt_rsa(content, user_email)
        
        print(f"Encrypted successfully with algorithm: {encrypted_result['algorithm']}")
        print(f"Encrypted content length: {len(encrypted_result['encrypted_content'])}")
        
        print("Decrypting with RSA+AES...")
        decrypted_result = await decrypt_rsa(
            encrypted_result['encrypted_content'],
            user_email,
            encrypted_result['metadata']
        )
        
        print(f"Decryption successful: {decrypted_result['decrypted_content'] == content}")
        print(f"Decrypted content: {decrypted_result['decrypted_content']}")
        return True
    except Exception as e:
        print(f"Level 4 RSA test failed: {e}")
        traceback.print_exc()
        return False

async def run_all_tests():
    """Run all encryption tests"""
    print("Starting QuMail encryption tests for all security levels...")
    
    results = []
    
    try:
        # Run Level 1 test
        level1_result = await test_level1_otp()
        results.append(("Level 1: Quantum OTP", level1_result))
    except Exception as e:
        print(f"Level 1 test exception: {e}")
        results.append(("Level 1: Quantum OTP", False))
    
    try:
        # Run Level 2 test
        level2_result = await test_level2_aes()
        results.append(("Level 2: AES-256-GCM", level2_result))
    except Exception as e:
        print(f"Level 2 test exception: {e}")
        results.append(("Level 2: AES-256-GCM", False))
    
    try:
        # Run Level 3 test
        level3_result = await test_level3_pqc()
        results.append(("Level 3: Post-Quantum Cryptography", level3_result))
    except Exception as e:
        print(f"Level 3 test exception: {e}")
        results.append(("Level 3: Post-Quantum Cryptography", False))
    
    try:
        # Run Level 4 test
        level4_result = await test_level4_rsa()
        results.append(("Level 4: Hybrid RSA+AES", level4_result))
    except Exception as e:
        print(f"Level 4 test exception: {e}")
        results.append(("Level 4: Hybrid RSA+AES", False))
    
    # Print summary
    print("\n=== Test Results Summary ===")
    all_passed = True
    for name, result in results:
        status = "PASSED" if result else "FAILED"
        all_passed = all_passed and result
        print(f"{name}: {status}")
    
    print(f"\nOverall test result: {'PASSED' if all_passed else 'FAILED'}")
    
    return all_passed

if __name__ == "__main__":
    asyncio.run(run_all_tests())