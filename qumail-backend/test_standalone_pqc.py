import asyncio
import logging
import os
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Direct import from level3_pqc module to avoid config dependencies
try:
    from app.services.encryption.level3_pqc import encrypt_pqc, decrypt_pqc, is_pqc_available
except ImportError as e:
    logger.error(f"Import error: {e}")
    sys.exit(1)

async def test_pqc():
    """Test PQC encryption without KM server dependencies"""
    print(f'PQC Available: {is_pqc_available()}')
    print('Testing Level 3 PQC encryption and decryption...')
    
    # Test content
    content = 'Hello, this is a test of the Level 3 Post-Quantum Cryptography!'
    user_email = 'test@example.com'
    
    # Monkey patch the KM client functions to return empty status
    import app.services.encryption.level3_pqc as pqc_module
    
    # Store original functions for restoration
    original_km1_check = pqc_module.km1_client.check_key_status
    original_km2_check = pqc_module.km2_client.check_key_status
    
    # Mock the functions to skip quantum enhancement
    async def mock_key_status(*args, **kwargs):
        return {"stored_key_count": 0}
    
    pqc_module.km1_client.check_key_status = mock_key_status
    pqc_module.km2_client.check_key_status = mock_key_status
    
    try:
        # Encrypt
        print('Encrypting...')
        encrypted_result = await encrypt_pqc(content, user_email)
        print(f'Encrypted successfully with algorithm: {encrypted_result["algorithm"]}')
        
        # Decrypt
        print('Decrypting...')
        decrypted_result = await decrypt_pqc(
            encrypted_result['encrypted_content'],
            user_email,
            encrypted_result['metadata']
        )
        print(f'Decrypted content: {decrypted_result["decrypted_content"]}')
        print('Test completed successfully!')
        
        # Print verification
        print(f"Message integrity check: {'PASSED' if decrypted_result['decrypted_content'] == content else 'FAILED'}")
        print(f"Algorithm used: {encrypted_result['algorithm']}")
        print(f"Security level: {encrypted_result['metadata']['security_level']}")
        print(f"PQC algorithms: {', '.join(encrypted_result['metadata']['pqc_algorithms'])}")
    finally:
        # Restore original functions
        pqc_module.km1_client.check_key_status = original_km1_check
        pqc_module.km2_client.check_key_status = original_km2_check

if __name__ == '__main__':
    asyncio.run(test_pqc())