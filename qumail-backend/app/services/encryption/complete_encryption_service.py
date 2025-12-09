"""
Complete Quantum Encryption Service
Handles all 4 security levels with real quantum keys from the key pool
"""
import logging
from typing import Dict, Any

# Import the TESTED encryption functions
from .level1_otp import encrypt_otp, decrypt_otp
from .level2_aes import encrypt_aes, decrypt_aes
from .level3_pqc import encrypt_pqc, decrypt_pqc
from .level4_rsa import encrypt_rsa, decrypt_rsa

logger = logging.getLogger(__name__)

class QuantumEncryptionService:
    """Complete encryption service using TESTED quantum encryption functions"""
    
    async def encrypt_level_1_otp(self, message: str, sender_email: str = "sender@qumail.com",
                                   receiver_email: str = "") -> Dict[str, Any]:
        """Level 1: Quantum One-Time Pad - Uses tested encrypt_otp"""
        try:
            logger.info(f"📧 EMAIL: Level 1 OTP encryption starting (message size: {len(message)} bytes, sender: {sender_email}, receiver: {receiver_email})")
            result = await encrypt_otp(message, sender_email, receiver_email=receiver_email)
            logger.info(f"📧 EMAIL: Level 1 OTP encryption completed with flow_id {result['metadata']['flow_id']}")
            return result
        except Exception as e:
            logger.error(f"📧 EMAIL: Level 1 OTP encryption failed: {e}")
            raise
    
    async def decrypt_level_1_otp(self, encrypted_data: str, metadata: dict, user_email: str = "receiver@qumail.com") -> bytes:
        """Level 1: Quantum One-Time Pad Decryption - Uses tested decrypt_otp"""
        try:
            logger.info(f"📧 EMAIL: Level 1 OTP decryption starting (user: {user_email})")
            result = await decrypt_otp(encrypted_data, user_email, metadata)
            # decrypt_otp returns a dict with 'decrypted_content', extract it
            decrypted_str = result.get('decrypted_content', '')
            return decrypted_str.encode('utf-8') if isinstance(decrypted_str, str) else decrypted_str
        except Exception as e:
            logger.error(f"📧 EMAIL: Level 1 OTP decryption failed: {e}")
            raise
    
    async def encrypt_level_2_aes(self, message: str, sender_email: str = "sender@qumail.com",
                                   receiver_email: str = "") -> Dict[str, Any]:
        """Level 2: Quantum-Aided AES-256-GCM - Uses tested encrypt_aes"""
        try:
            logger.info(f"📧 EMAIL: Level 2 AES encryption starting (message size: {len(message)} bytes, sender: {sender_email}, receiver: {receiver_email})")
            result = await encrypt_aes(message, sender_email, receiver_email=receiver_email)
            logger.info(f"📧 EMAIL: Level 2 AES encryption completed with flow_id {result['metadata']['flow_id']}")
            return result
        except Exception as e:
            logger.error(f"📧 EMAIL: Level 2 AES encryption failed: {e}")
            raise
    
    async def decrypt_level_2_aes(self, encrypted_data: str, metadata: dict, user_email: str = "receiver@qumail.com") -> bytes:
        """Level 2: Quantum-Aided AES-256-GCM Decryption - Uses tested decrypt_aes"""
        try:
            logger.info(f"📧 EMAIL: Level 2 AES decryption starting (user: {user_email})")
            result = await decrypt_aes(encrypted_data, user_email, metadata)
            # decrypt_aes returns a dict with 'decrypted_content', extract it
            decrypted_str = result.get('decrypted_content', '')
            return decrypted_str.encode('utf-8') if isinstance(decrypted_str, str) else decrypted_str
        except Exception as e:
            logger.error(f"📧 EMAIL: Level 2 AES decryption failed: {e}")
            raise
    
    async def encrypt_level_3_pqc(self, message: str, sender_email: str = "sender@qumail.com",
                                   receiver_email: str = "") -> Dict[str, Any]:
        """Level 3: Post-Quantum Cryptography - Uses tested encrypt_pqc"""
        try:
            logger.info(f"📧 EMAIL: Level 3 PQC encryption starting (message size: {len(message)} bytes, sender: {sender_email}, receiver: {receiver_email})")
            result = await encrypt_pqc(message, sender_email, receiver_email=receiver_email)
            logger.info(f"📧 EMAIL: Level 3 PQC encryption completed with flow_id {result['metadata']['flow_id']}")
            return result
        except Exception as e:
            logger.error(f"📧 EMAIL: Level 3 PQC encryption failed: {e}")
            raise
    
    async def decrypt_level_3_pqc(self, encrypted_data: str, metadata: dict, user_email: str = "receiver@qumail.com") -> bytes:
        """Level 3: Post-Quantum Cryptography Decryption - Uses tested decrypt_pqc"""
        try:
            logger.info(f"📧 EMAIL: Level 3 PQC decryption starting (user: {user_email})")
            result = await decrypt_pqc(encrypted_data, user_email, metadata)
            # decrypt_pqc returns a dict with 'decrypted_content', extract it
            decrypted_str = result.get('decrypted_content', '')
            return decrypted_str.encode('utf-8') if isinstance(decrypted_str, str) else decrypted_str
        except Exception as e:
            logger.error(f"📧 EMAIL: Level 3 PQC decryption failed: {e}")
            raise
    
    async def encrypt_level_4_standard(self, message: str, sender_email: str = "sender@qumail.com",
                                        receiver_email: str = "") -> Dict[str, Any]:
        """Level 4: Standard RSA Encryption - Uses tested encrypt_rsa"""
        try:
            logger.info(f"📧 EMAIL: Level 4 RSA encryption starting (message size: {len(message)} bytes, sender: {sender_email}, receiver: {receiver_email})")
            result = await encrypt_rsa(message, sender_email, receiver_email=receiver_email)
            logger.info(f"📧 EMAIL: Level 4 RSA encryption completed with flow_id {result['metadata']['flow_id']}")
            return result
        except Exception as e:
            logger.error(f"📧 EMAIL: Level 4 RSA encryption failed: {e}")
            raise
    
    async def decrypt_level_4_standard(self, encrypted_data: str, metadata: dict, user_email: str = "receiver@qumail.com") -> bytes:
        """Level 4: Standard RSA Decryption - Uses tested decrypt_rsa"""
        try:
            logger.info(f"📧 EMAIL: Level 4 RSA decryption starting (user: {user_email})")
            result = await decrypt_rsa(encrypted_data, user_email, metadata)
            # decrypt_rsa returns a dict with 'decrypted_content', extract it
            decrypted_str = result.get('decrypted_content', '')
            return decrypted_str.encode('utf-8') if isinstance(decrypted_str, str) else decrypted_str
        except Exception as e:
            logger.error(f"📧 EMAIL: Level 4 RSA decryption failed: {e}")
            raise

# Global encryption service instance
complete_encryption_service = QuantumEncryptionService()
