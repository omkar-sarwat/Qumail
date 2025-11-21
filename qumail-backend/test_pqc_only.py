import asyncio
import logging
import traceback
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def run_module_test(module_name, encrypt_func, decrypt_func, message):
    """Run a test for a specific encryption module"""
    try:
        print(f"\n=== Testing {module_name} ===")
        print(f"Message: {message}")
        
        print("Encrypting...")
        encrypted_result = asyncio.run(encrypt_func(message, "test@example.com"))
        
        print(f"Encrypted successfully with algorithm: {encrypted_result.get('algorithm', 'unknown')}")
        print(f"Encrypted content length: {len(encrypted_result.get('encrypted_content', ''))}")
        
        print("Decrypting...")
        decrypted_result = asyncio.run(decrypt_func(
            encrypted_result['encrypted_content'],
            "test@example.com",
            encrypted_result['metadata']
        ))
        
        print(f"Decryption successful: {decrypted_result.get('decrypted_content', '') == message}")
        print(f"Decrypted content: {decrypted_result.get('decrypted_content', '')}")
        return True
    except Exception as e:
        print(f"{module_name} test failed: {e}")
        traceback.print_exc()
        return False

def test_level3_pqc():
    """Test Level 3: Post-Quantum Cryptography"""
    try:
        from app.services.encryption.level3_pqc import encrypt_pqc, decrypt_pqc, is_pqc_available
        print(f"PQC Available: {is_pqc_available()}")
        return run_module_test(
            "Level 3: Post-Quantum Cryptography",
            encrypt_pqc,
            decrypt_pqc,
            "This is a Level 3 Post-Quantum encrypted message that's resistant to quantum computers!"
        )
    except ImportError:
        print("Level 3 PQC module not available")
        return False

if __name__ == "__main__":
    # Run only the Level 3 PQC test
    success = test_level3_pqc()
    
    if success:
        print("\n=== Test completed successfully! ===")
        sys.exit(0)
    else:
        print("\n=== Test failed! ===")
        sys.exit(1)