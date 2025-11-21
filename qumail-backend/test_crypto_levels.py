import asyncio
import sys
import os
import logging
import base64
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import encryption services
# We need to make sure we can import from app.services.encryption
try:
    from app.services.encryption.level1_otp import encrypt_otp, decrypt_otp
    from app.services.encryption.level2_aes import encrypt_aes, decrypt_aes
    from app.services.encryption.level3_pqc import encrypt_pqc, decrypt_pqc
    from app.services.encryption.level4_rsa import encrypt_rsa, decrypt_rsa
    from app.services.km_client_init import use_optimized_km_clients
except ImportError as e:
    logger.error(f"Import failed: {e}")
    logger.info("Attempting to adjust path...")
    sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    from app.services.encryption.level1_otp import encrypt_otp, decrypt_otp
    from app.services.encryption.level2_aes import encrypt_aes, decrypt_aes
    from app.services.encryption.level3_pqc import encrypt_pqc, decrypt_pqc
    from app.services.encryption.level4_rsa import encrypt_rsa, decrypt_rsa
    from app.services.km_client_init import use_optimized_km_clients

async def test_level1_otp():
    logger.info("\n" + "="*50)
    logger.info("TESTING LEVEL 1: OTP (One-Time Pad)")
    logger.info("="*50)
    
    user_email = "test_user@example.com"
    content = "This is a secret message for Level 1 OTP."
    
    try:
        # Encrypt
        logger.info("Encrypting...")
        enc_result = await encrypt_otp(content, user_email)
        logger.info(f"Encryption successful. Algorithm: {enc_result['algorithm']}")
        logger.info(f"Auth Tag: {enc_result.get('auth_tag', 'N/A')}")
        
        # Decrypt
        logger.info("Decrypting...")
        dec_result = await decrypt_otp(
            enc_result['encrypted_content'], 
            user_email, 
            enc_result['metadata']
        )
        
        if dec_result['decrypted_content'] == content:
            logger.info("✅ Level 1 OTP Test PASSED: Content matches")
        else:
            logger.error("❌ Level 1 OTP Test FAILED: Content mismatch")
            logger.error(f"Expected: {content}")
            logger.error(f"Got: {dec_result['decrypted_content']}")
            
    except Exception as e:
        logger.error(f"❌ Level 1 OTP Test FAILED with error: {e}")

async def test_level2_aes():
    logger.info("\n" + "="*50)
    logger.info("TESTING LEVEL 2: AES-256-GCM")
    logger.info("="*50)
    
    user_email = "test_user@example.com"
    content = "This is a secret message for Level 2 AES."
    
    try:
        # Encrypt
        logger.info("Encrypting...")
        enc_result = await encrypt_aes(content, user_email)
        logger.info(f"Encryption successful. Algorithm: {enc_result['algorithm']}")
        logger.info(f"Auth Tag: {enc_result.get('auth_tag', 'N/A')}")
        
        # Decrypt
        logger.info("Decrypting...")
        dec_result = await decrypt_aes(
            enc_result['encrypted_content'], 
            user_email, 
            enc_result['metadata']
        )
        
        if dec_result['decrypted_content'] == content:
            logger.info("✅ Level 2 AES Test PASSED: Content matches")
        else:
            logger.error("❌ Level 2 AES Test FAILED: Content mismatch")
            
    except Exception as e:
        logger.error(f"❌ Level 2 AES Test FAILED with error: {e}")

async def test_level3_pqc():
    logger.info("\n" + "="*50)
    logger.info("TESTING LEVEL 3: PQC (Kyber + Dilithium)")
    logger.info("="*50)
    
    user_email = "test_user@example.com"
    content = "This is a secret message for Level 3 PQC."
    
    try:
        # Encrypt
        logger.info("Encrypting...")
        enc_result = await encrypt_pqc(content, user_email)
        logger.info(f"Encryption successful. Algorithm: {enc_result['algorithm']}")
        logger.info(f"Signature: {enc_result.get('signature', 'N/A')[:20]}...")
        
        # Verify Signature presence
        if not enc_result.get('signature'):
            logger.error("❌ Level 3 PQC Test FAILED: Missing Signature")
            return

        # Decrypt
        logger.info("Decrypting...")
        dec_result = await decrypt_pqc(
            enc_result['encrypted_content'], 
            user_email, 
            enc_result['metadata']
        )
        
        if dec_result['decrypted_content'] == content:
            logger.info("✅ Level 3 PQC Test PASSED: Content matches")
        else:
            logger.error("❌ Level 3 PQC Test FAILED: Content mismatch")
            
    except Exception as e:
        logger.error(f"❌ Level 3 PQC Test FAILED with error: {e}")

async def test_level4_rsa():
    logger.info("\n" + "="*50)
    logger.info("TESTING LEVEL 4: RSA-4096 + AES")
    logger.info("="*50)
    
    user_email = "test_user@example.com"
    content = "This is a secret message for Level 4 RSA."
    
    try:
        # Encrypt
        logger.info("Encrypting...")
        enc_result = await encrypt_rsa(content, user_email)
        logger.info(f"Encryption successful. Algorithm: {enc_result['algorithm']}")
        logger.info(f"Signature: {enc_result.get('signature', 'N/A')[:20]}...")
        
        # Verify Signature presence
        if not enc_result.get('signature'):
            logger.error("❌ Level 4 RSA Test FAILED: Missing Signature")
            return

        # Decrypt
        logger.info("Decrypting...")
        dec_result = await decrypt_rsa(
            enc_result['encrypted_content'], 
            user_email, 
            enc_result['metadata']
        )
        
        if dec_result['decrypted_content'] == content:
            logger.info("✅ Level 4 RSA Test PASSED: Content matches")
        else:
            logger.error("❌ Level 4 RSA Test FAILED: Content mismatch")
            
    except Exception as e:
        logger.error(f"❌ Level 4 RSA Test FAILED with error: {e}")

async def main():
    # Initialize KM clients
    # We assume environment variables are set for Cloud KMEs if needed
    # or that the default configuration points to the correct location.
    
    logger.info("Initializing KM Clients...")
    try:
        use_optimized_km_clients()
    except Exception as e:
        logger.warning(f"Could not initialize KM clients: {e}")
        logger.warning("Tests requiring KME might fail if not mocked.")

    await test_level1_otp()
    await test_level2_aes()
    await test_level3_pqc()
    await test_level4_rsa()

if __name__ == "__main__":
    asyncio.run(main())
