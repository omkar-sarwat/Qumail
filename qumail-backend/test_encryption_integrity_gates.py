import asyncio
import logging
import os
import sys
import base64
import traceback
import uuid
import datetime
import secrets
import hmac
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock KM client functions
async def mock_key_status(*args, **kwargs):
    return {"stored_key_count": 100}  # Indicate plenty of keys available

async def mock_request_enc_keys(*args, **kwargs):
    # Return simulated quantum key data with proper size
    # For Level 1, size might be passed as bits, but we need to handle the L+32 requirement if it comes from the caller
    # The caller (level1_otp.py) calculates the size it needs.
    size_bits = kwargs.get('size', 256)
    size_bytes = size_bits // 8
    
    key_id = str(uuid.uuid4())
    key_data = os.urandom(size_bytes)
    key_storage[key_id] = key_data
    return [{"key": base64.b64encode(key_data).decode(), "key_ID": key_id}]

async def mock_request_dec_keys(*args, **kwargs):
    key_id = kwargs.get('key_ID')
    if key_id and key_id in key_storage:
        key_data = key_storage[key_id]
        return [{"key": base64.b64encode(key_data).decode(), "key_ID": key_id}]
    
    # Fallback if key not found (shouldn't happen in correct flow)
    size_bits = kwargs.get('size', 256)
    size_bytes = size_bits // 8
    return [{"key": base64.b64encode(os.urandom(size_bytes)).decode(), "key_ID": key_id or str(uuid.uuid4())}]

async def mock_mark_key_consumed(*args, **kwargs):
    key_id = kwargs.get('key_ID') or args[0] if args else None
    if key_id and key_id in key_storage:
        # In a real system we'd delete it, but for testing we might want to keep it if we re-run
        # del key_storage[key_id] 
        pass
    return True

# Store key mappings for encryption/decryption consistency
key_storage = {}

# Apply mocks to avoid KM server dependency
def apply_mocks():
    try:
        import app.services.km_client as km_client_module
        
        # Store original functions
        original_funcs = {}
        original_funcs['km1_check'] = km_client_module.km1_client.check_key_status
        original_funcs['km2_check'] = km_client_module.km2_client.check_key_status
        original_funcs['km1_enc'] = km_client_module.km1_client.request_enc_keys
        original_funcs['km2_enc'] = km_client_module.km2_client.request_enc_keys
        original_funcs['km1_dec'] = km_client_module.km1_client.request_dec_keys
        original_funcs['km2_dec'] = km_client_module.km2_client.request_dec_keys
        original_funcs['km1_mark'] = km_client_module.km1_client.mark_key_consumed
        original_funcs['km2_mark'] = km_client_module.km2_client.mark_key_consumed
        
        # Apply mocks
        km_client_module.km1_client.check_key_status = mock_key_status
        km_client_module.km2_client.check_key_status = mock_key_status
        km_client_module.km1_client.request_enc_keys = mock_request_enc_keys
        km_client_module.km2_client.request_enc_keys = mock_request_enc_keys
        km_client_module.km1_client.request_dec_keys = mock_request_dec_keys
        km_client_module.km2_client.request_dec_keys = mock_request_dec_keys
        km_client_module.km1_client.mark_key_consumed = mock_mark_key_consumed
        km_client_module.km2_client.mark_key_consumed = mock_mark_key_consumed
        
        return original_funcs
    except ImportError as e:
        logger.error(f"Failed to apply mocks: {e}")
        return None

# Restore original functions
def restore_mocks(original_funcs):
    if not original_funcs:
        return
        
    try:
        import app.services.km_client as km_client_module
        
        # Restore original functions
        km_client_module.km1_client.check_key_status = original_funcs['km1_check']
        km_client_module.km2_client.check_key_status = original_funcs['km2_check']
        km_client_module.km1_client.request_enc_keys = original_funcs['km1_enc']
        km_client_module.km2_client.request_enc_keys = original_funcs['km2_enc']
        km_client_module.km1_client.request_dec_keys = original_funcs['km1_dec']
        km_client_module.km2_client.request_dec_keys = original_funcs['km2_dec']
        km_client_module.km1_client.mark_key_consumed = original_funcs['km1_mark']
        km_client_module.km2_client.mark_key_consumed = original_funcs['km2_mark']
    except ImportError as e:
        logger.error(f"Failed to restore mocks: {e}")

async def test_level1_otp():
    """Test Level 1: Quantum One-Time Pad encryption with Split Key Integrity Gate"""
    print("\n=== Testing Level 1: Quantum One-Time Pad (Split Key) ===")
    try:
        from app.services.encryption.level1_otp import encrypt_otp, decrypt_otp
        
        content = "This is a Level 1 OTP encrypted message with Split Key Integrity Gate!"
        user_email = "test@example.com"
        
        print("Encrypting with OTP...")
        encrypted_result = await encrypt_otp(content, user_email)
        
        print(f"Encrypted successfully with algorithm: {encrypted_result['algorithm']}")
        print(f"Encrypted content length: {len(encrypted_result['encrypted_content'])}")
        
        # Verify metadata contains auth_tag
        metadata = encrypted_result['metadata']
        if 'auth_tag' not in metadata:
            print("FAILED: auth_tag missing from metadata")
            return False
        print(f"Auth Tag present: {metadata['auth_tag']}")
        
        print("Decrypting with OTP...")
        decrypted_result = await decrypt_otp(
            encrypted_result['encrypted_content'],
            user_email,
            metadata
        )
        
        success = decrypted_result['decrypted_content'] == content
        print(f"Decryption successful: {success}")
        print(f"Decrypted content: {decrypted_result['decrypted_content']}")
        
        # Test Integrity Gate: Tamper with content
        print("Testing Integrity Gate (Tampering)...")
        tampered_content = base64.b64encode(base64.b64decode(encrypted_result['encrypted_content'])[:-1] + b'0').decode()
        try:
            await decrypt_otp(tampered_content, user_email, metadata)
            print("FAILED: Tampered content was accepted!")
            success = False
        except Exception as e:
            print(f"Integrity Gate worked! Caught expected error: {e}")
            
        return success
    except Exception as e:
        print(f"Level 1 OTP test failed: {e}")
        traceback.print_exc()
        return False

async def test_level2_aes():
    """Test Level 2: AES-256-GCM encryption with Integrity Gate"""
    print("\n=== Testing Level 2: AES-256-GCM (Integrity Gate) ===")
    try:
        from app.services.encryption.level2_aes import encrypt_aes, decrypt_aes
        
        content = "This is a Level 2 AES encrypted message with Integrity Gate!"
        user_email = "test@example.com"
        
        print("Encrypting with AES-256-GCM...")
        encrypted_result = await encrypt_aes(content, user_email)
        
        print(f"Encrypted successfully with algorithm: {encrypted_result['algorithm']}")
        
        # Verify metadata contains auth_tag
        metadata = encrypted_result['metadata']
        if 'auth_tag' not in metadata:
            print("FAILED: auth_tag missing from metadata")
            return False
        print(f"Auth Tag present: {metadata['auth_tag']}")
        
        print("Decrypting with AES-256-GCM...")
        decrypted_result = await decrypt_aes(
            encrypted_result['encrypted_content'],
            user_email,
            metadata
        )
        
        success = decrypted_result['decrypted_content'] == content
        print(f"Decryption successful: {success}")
        
        # Test Integrity Gate: Tamper with auth_tag
        print("Testing Integrity Gate (Tampering Auth Tag)...")
        tampered_metadata = metadata.copy()
        # Flip a bit in the auth tag
        tag_bytes = bytearray(base64.b64decode(tampered_metadata['auth_tag']))
        tag_bytes[0] ^= 0xFF
        tampered_metadata['auth_tag'] = base64.b64encode(tag_bytes).decode()
        
        try:
            await decrypt_aes(encrypted_result['encrypted_content'], user_email, tampered_metadata)
            print("FAILED: Tampered auth_tag was accepted!")
            success = False
        except Exception as e:
            print(f"Integrity Gate worked! Caught expected error: {e}")
            
        return success
    except Exception as e:
        print(f"Level 2 AES test failed: {e}")
        traceback.print_exc()
        return False

async def test_level3_pqc():
    """Test Level 3: Post-Quantum Cryptography with Integrity Gate"""
    print("\n=== Testing Level 3: Post-Quantum Cryptography (Integrity Gate) ===")
    try:
        from app.services.encryption.level3_pqc import encrypt_pqc, decrypt_pqc
        
        content = "This is a Level 3 PQC encrypted message with Integrity Gate!"
        user_email = "test@example.com"
        
        print("Encrypting with PQC...")
        encrypted_result = await encrypt_pqc(content, user_email)
        
        print(f"Encrypted successfully with algorithm: {encrypted_result['algorithm']}")
        
        # Verify metadata contains auth_tag
        metadata = encrypted_result['metadata']
        if 'auth_tag' not in metadata:
            print("FAILED: auth_tag missing from metadata")
            return False
        print(f"Auth Tag present: {metadata['auth_tag']}")
        
        print("Decrypting with PQC...")
        decrypted_result = await decrypt_pqc(
            encrypted_result['encrypted_content'],
            user_email,
            metadata
        )
        
        success = decrypted_result['decrypted_content'] == content
        print(f"Decryption successful: {success}")
        
        return success
    except Exception as e:
        print(f"Level 3 PQC test failed: {e}")
        traceback.print_exc()
        return False

async def test_level4_rsa():
    """Test Level 4: Hybrid RSA+AES encryption with Integrity Gate"""
    print("\n=== Testing Level 4: Hybrid RSA+AES (Integrity Gate) ===")
    try:
        from app.services.encryption.level4_rsa import encrypt_rsa, decrypt_rsa
        
        content = "This is a Level 4 RSA+AES hybrid encrypted message with Integrity Gate!"
        user_email = "test@example.com"
        
        print("Encrypting with RSA+AES...")
        encrypted_result = await encrypt_rsa(content, user_email)
        
        print(f"Encrypted successfully with algorithm: {encrypted_result['algorithm']}")
        
        # Verify metadata contains auth_tag
        metadata = encrypted_result['metadata']
        if 'auth_tag' not in metadata:
            print("FAILED: auth_tag missing from metadata")
            return False
        print(f"Auth Tag present: {metadata['auth_tag']}")
        
        print("Decrypting with RSA+AES...")
        decrypted_result = await decrypt_rsa(
            encrypted_result['encrypted_content'],
            user_email,
            metadata
        )
        
        success = decrypted_result['decrypted_content'] == content
        print(f"Decryption successful: {success}")
        
        return success
    except Exception as e:
        print(f"Level 4 RSA test failed: {e}")
        traceback.print_exc()
        return False

async def run_all_tests():
    """Run all encryption tests with KM server mocks"""
    print("="*80)
    print("  QUMAIL SECURE EMAIL - INTEGRITY GATES TEST SUITE")
    print("  (Running with mocked KM servers - no actual QKD required)")
    print("="*80)
    
    # Apply mocks to KM clients
    original_funcs = apply_mocks()
    
    results = {}
    
    try:
        # Test all four encryption levels
        results["Level 1: Quantum OTP"] = await test_level1_otp()
        results["Level 2: AES-256-GCM"] = await test_level2_aes()
        results["Level 3: Post-Quantum"] = await test_level3_pqc()
        results["Level 4: RSA+AES"] = await test_level4_rsa()
        
        # Print results summary
        print("\n" + "="*50)
        print("  TEST RESULTS SUMMARY")
        print("="*50)
        
        all_passed = True
        for name, success in results.items():
            status = "PASSED" if success else "FAILED"
            all_passed = all_passed and success
            print(f"{name}: {status}")
        
        print("\n" + "="*50)
        print(f"  OVERALL TEST STATUS: {'PASSED' if all_passed else 'FAILED'}")
        print("="*50)
        
        return all_passed
    finally:
        # Always restore original KM client functions
        restore_mocks(original_funcs)

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
