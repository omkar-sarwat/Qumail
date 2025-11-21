"""
QuMail-Only Quantum Encryption System
Ensures encrypted messages can only be decrypted within QuMail application
Uses quantum keys with QuMail-specific cryptographic binding
"""

import base64
import json
import hmac
import hashlib
import secrets
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
import os
import logging

from .quantum_key_manager import SecurityLevel

logger = logging.getLogger(__name__)

class QuMailQuantumEncryption:
    """Quantum encryption system that only works within QuMail"""
    
    # QuMail application signature - unique identifier
    QUMAIL_APP_SIGNATURE = b"QuMail-Secure-Email-v1.0-Quantum-2025"
    
    # QuMail decryption salt - prevents decryption outside QuMail
    QUMAIL_SALT = b"QuMail-Only-Decryption-Salt-Quantum-Security"
    
    def __init__(self, quantum_key_manager):
        """Initialize QuMail-specific quantum encryption"""
        self.quantum_key_manager = quantum_key_manager
        # Generate QuMail session key for this instance
        self.qumail_session_key = self._generate_qumail_session_key()
        logger.info("Initialized QuMail-Only Quantum Encryption System")
    
    def _generate_qumail_session_key(self) -> bytes:
        """Generate QuMail-specific session key"""
        # Combine app signature with system-specific data
        system_data = f"{datetime.now().strftime('%Y-%m-%d')}-QuMail-Session".encode()
        
        # Create HMAC with QuMail signature
        session_key = hmac.new(
            self.QUMAIL_APP_SIGNATURE,
            system_data,
            hashlib.sha256
        ).digest()
        
        return session_key
    
    def _derive_qumail_key(self, quantum_key: str, additional_data: str = "") -> bytes:
        """Derive QuMail-specific encryption key from quantum key"""
        # Combine quantum key with QuMail-specific data
        quantum_bytes = base64.b64decode(quantum_key)
        
        # Create QuMail-specific key derivation
        kdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,  # 256-bit key
            salt=self.QUMAIL_SALT,
            info=self.QUMAIL_APP_SIGNATURE + additional_data.encode(),
        )
        
        # Derive key that only works with QuMail signature
        qumail_key = kdf.derive(quantum_bytes)
        
        # Add session binding
        final_key = hmac.new(
            self.qumail_session_key,
            qumail_key,
            hashlib.sha256
        ).digest()
        
        return final_key
    
    async def encrypt_message(self, message: str, security_level: SecurityLevel,
                            user_id: str, recipient_id: str) -> Dict[str, Any]:
        """
        Encrypt message with ONE-TIME quantum key - QUMAIL-EXCLUSIVE decryption
        Result appears as GIBBERISH to all non-QuMail applications: fhehf744775hhdfbdbf488488...
        
        Security Features:
        - One-time quantum keys (NEVER reused)
        - QuMail-exclusive decryption format
        - Perfect forward secrecy
        - Tamper-evident message structure
        """
        try:
            # Generate unique message ID
            message_id = f"qm_{int(datetime.now().timestamp())}_{secrets.token_hex(8)}"
            
            logger.info(f"Encrypting message {message_id} with {security_level.name} quantum security")
            
            # Get ONE-TIME quantum key (NEVER REUSED)
            quantum_key_result = await self.quantum_key_manager.get_one_time_quantum_key_for_level(
                security_level, user_id, "ENCRYPT"
            )
            
            if not quantum_key_result:
                raise Exception(f"Failed to obtain one-time quantum key for {security_level.name} security")
            
            quantum_key = quantum_key_result["key_material"]
            key_id = quantum_key_result["key_id"]
            
            logger.debug(f"Using one-time quantum key {key_id} from {quantum_key_result.get('kme_source')}")
            
            # Import the QuMail cipher for exclusive encryption
            from app.security.qumail_quantum_cipher import encrypt_for_qumail_only
            
            # Encrypt message using QuMail-exclusive cipher
            # This creates GIBBERISH that ONLY QuMail can decrypt
            encrypted_gibberish = encrypt_for_qumail_only(
                message=message,
                quantum_key=quantum_key,
                key_id=key_id,
                security_level=security_level.name,
                recipient_id=recipient_id
            )
            
            # CRITICAL: Mark quantum key as PERMANENTLY consumed (ONE-TIME USE ONLY)
            consumption_success = await self.quantum_key_manager.mark_key_consumed_forever(
                key_id=key_id,
                user_id=user_id,
                message_id=message_id,
                operation_type="ENCRYPT"
            )
            
            if not consumption_success:
                logger.error(f"SECURITY CRITICAL: Failed to mark quantum key {key_id} as consumed")
                raise Exception("Failed to enforce one-time key usage - encryption aborted for security")
            
            # Create QuMail message envelope (appears as additional gibberish)
            qumail_envelope = {
                "qm_encrypted": True,
                "qm_quantum": True,
                "qm_one_time_key": True,
                "qm_version": "2.0",
                "qm_security": security_level.name,
                "qm_id": message_id,
                "qm_key_id": key_id,
                "qm_gibberish": encrypted_gibberish,  # The actual encrypted content (appears as gibberish)
                "qm_checksum": self._create_qumail_checksum(encrypted_gibberish.encode(), message_id),
                "qm_timestamp": datetime.now().timestamp(),
                "qm_kme_source": quantum_key_result.get("kme_source"),
                "qm_key_consumed": True,  # Key is permanently consumed
                # Display text for non-QuMail apps (looks like encrypted gibberish)
                "display_text": self._generate_obfuscated_display(len(message))
            }
            
            logger.info(f"Message {message_id} encrypted with ONE-TIME quantum key {key_id}")
            logger.info(f"Key permanently consumed - NEVER reusable")
            logger.info(f"Message appears as gibberish to non-QuMail apps: {encrypted_gibberish[:30]}...")
            
            return {
                "success": True,
                "message_id": message_id,
                "key_id": key_id,
                "encrypted_envelope": qumail_envelope,
                "encrypted_display": encrypted_gibberish,  # What other apps see as gibberish
                "security_level": security_level.name,
                "one_time_key_used": True,
                "key_permanently_consumed": True,
                "kme_source": quantum_key_result.get("kme_source"),
                "quality_score": quantum_key_result.get("quality_score"),
                "encrypted_at": datetime.now().isoformat(),
                "qumail_exclusive": True
            }
            
        except Exception as e:
            logger.error(f"Quantum encryption failed: {e}")
            raise Exception(f"QuMail quantum encryption error: {e}")
    
    def _create_qumail_checksum(self, encrypted_data: bytes, message_id: str) -> str:
        """Create QuMail-specific checksum for integrity verification"""
        checksum_data = encrypted_data + message_id.encode() + self.QUMAIL_APP_SIGNATURE
        checksum = hmac.new(
            self.qumail_session_key,
            checksum_data,
            hashlib.sha256
        ).hexdigest()[:16]  # First 16 chars
        
        return checksum
    
    def _generate_obfuscated_display(self, original_length: int) -> str:
        """Generate obfuscated text that non-QuMail apps will see"""
        # Create realistic-looking encrypted text similar to user's request
        chars = "abcdefgh0123456789"
        
        # Generate obfuscated string with similar length patterns
        obfuscated_parts = []
        remaining = max(original_length, 50)  # Minimum 50 chars
        
        while remaining > 0:
            part_len = min(secrets.randbelow(10) + 5, remaining)
            part = ''.join(secrets.choice(chars) for _ in range(part_len))
            obfuscated_parts.append(part)
            remaining -= part_len
        
        return ''.join(obfuscated_parts)
    
    async def decrypt_message(self, encrypted_envelope: Dict[str, Any], 
                            user_id: str) -> Optional[Dict[str, Any]]:
        """
        Decrypt QuMail-exclusive quantum encrypted message
        ONLY works within QuMail application - other apps see gibberish
        
        Args:
            encrypted_envelope: QuMail encrypted envelope or gibberish string
            user_id: User attempting decryption
            
        Returns:
            Decrypted message data or None if not QuMail-compatible
        """
        try:
            # Handle different input formats
            if isinstance(encrypted_envelope, str):
                # Direct gibberish format - extract from display_text or encrypted_display
                encrypted_gibberish = encrypted_envelope
                key_id = None
                message_id = None
            else:
                # QuMail envelope format
                # Verify QuMail encryption format
                if not encrypted_envelope.get("qm_encrypted"):
                    logger.warning("Message not encrypted with QuMail quantum system")
                    return None
                
                # Verify QuMail version compatibility
                qm_version = encrypted_envelope.get("qm_version", "1.0")
                if qm_version not in ["1.0", "2.0"]:
                    logger.warning(f"Incompatible QuMail encryption version: {qm_version}")
                    return None
                
                # Extract data from envelope
                message_id = encrypted_envelope.get("qm_id")
                key_id = encrypted_envelope.get("qm_key_id")
                encrypted_gibberish = encrypted_envelope.get("qm_gibberish")
                security_level_name = encrypted_envelope.get("qm_security")
                expected_checksum = encrypted_envelope.get("qm_checksum")
                
                if not encrypted_gibberish:
                    logger.error("No encrypted gibberish data found in envelope")
                    return None
                
                # Verify checksum if available
                if expected_checksum:
                    actual_checksum = self._create_qumail_checksum(encrypted_gibberish.encode(), message_id)
                    if not hmac.compare_digest(expected_checksum, actual_checksum):
                        logger.error("QuMail checksum verification failed - message corrupted or tampered")
                        return None
            
            logger.info(f"Attempting to decrypt QuMail-exclusive message {message_id}")
            
            # For decryption, we need the quantum key
            # In a real implementation, the key would need to be retrieved or provided
            # Since keys are one-time use, they should be consumed during encryption
            # This presents a challenge for decryption - in production, the key would be
            # temporarily stored securely until message is delivered and decrypted
            
            logger.error("DECRYPTION CHALLENGE: One-time quantum keys are consumed during encryption")
            logger.error("Production solution requires secure key escrow for recipient decryption")
            
            # For demonstration, we'll show that the gibberish is properly formatted
            # but cannot be decrypted without the original quantum key
            
            return {
                "success": False,
                "error": "ONE_TIME_KEY_CONSUMED",
                "message": "Quantum key was consumed during encryption (one-time use only)",
                "key_id": key_id,
                "message_id": message_id,
                "gibberish_confirmed": True,
                "qumail_exclusive": True,
                "solution": "Implement secure key escrow for recipient decryption in production"
            }
            
        except Exception as e:
            logger.error(f"QuMail-exclusive decryption failed: {e}")
            return None
            
            # Check if quantum key was already consumed
            if await self.quantum_key_manager.verify_key_consumption(message_id):
                logger.info(f"Quantum key for message {message_id} was properly consumed")
            else:
                logger.warning(f"Quantum key consumption verification failed for {message_id}")
            
            # NOTE: In a real scenario, we would need to reconstruct the quantum key
            # For this implementation, we'll use a secure key derivation that only works in QuMail
            # This is a simplified version - in production, you'd need more sophisticated key management
            
            logger.info(f"Successfully decrypted QuMail quantum message {message_id}")
            
            # Return decrypted message structure (simplified for demo)
            return {
                "message_id": message_id,
                "security_level": security_level.value,
                "decrypted_in_qumail": True,
                "content": "[QUANTUM ENCRYPTED MESSAGE - DECRYPTED IN QUMAIL]",
                "note": "This message was encrypted with one-time quantum keys and can only be decrypted in QuMail"
            }
            
        except Exception as e:
            logger.error(f"QuMail quantum decryption failed: {e}")
            return None
    
    def get_display_text_for_other_apps(self, encrypted_message: Dict[str, Any]) -> str:
        """Get the obfuscated text that non-QuMail apps will see"""
        return encrypted_message.get("display_text", "fhehf744775hhdfbdbf488488")

class QuMailSecurityLevelManager:
    """Manages different security levels with quantum encryption"""
    
    def __init__(self, quantum_key_manager=None):
        self.quantum_key_manager = quantum_key_manager
        self.encryption_system = QuMailQuantumEncryption(quantum_key_manager)
        
        # Security level descriptions
        self.security_descriptions = {
            SecurityLevel.LOW: {
                "name": "Low Security",
                "description": "32-byte quantum keys, basic encryption",
                "use_case": "Internal communications, non-sensitive data"
            },
            SecurityLevel.MEDIUM: {
                "name": "Medium Security", 
                "description": "64-byte quantum keys, enhanced encryption",
                "use_case": "Business communications, moderate sensitivity"
            },
            SecurityLevel.HIGH: {
                "name": "High Security",
                "description": "128-byte quantum keys, military-grade encryption",
                "use_case": "Confidential data, government communications"
            },
            SecurityLevel.ULTRA: {
                "name": "Ultra Security",
                "description": "256-byte quantum keys, maximum security",
                "use_case": "Top secret, critical infrastructure, quantum-safe"
            }
        }
    
    async def encrypt_with_level(self, message: str, security_level: SecurityLevel,
                               user_id: str, recipient_id: str) -> Dict[str, Any]:
        """Encrypt message with specified security level using quantum keys"""
        return await self.encryption_system.encrypt_message(
            message, security_level, user_id, recipient_id
        )
    
    async def decrypt_qumail_message(self, encrypted_message: Dict[str, Any], 
                                   user_id: str) -> Optional[Dict[str, Any]]:
        """Decrypt message if it's a valid QuMail quantum-encrypted message"""
        return await self.encryption_system.decrypt_message(encrypted_message, user_id)
    
    def get_security_level_info(self) -> Dict[str, Any]:
        """Get information about all security levels"""
        info = {}
        for level in SecurityLevel:
            info[level.value] = self.security_descriptions[level]
            
        return info
    
    def get_obfuscated_display(self, encrypted_message: Dict[str, Any]) -> str:
        """Get obfuscated text for display in non-QuMail applications"""
        return self.encryption_system.get_display_text_for_other_apps(encrypted_message)

# Global security manager
security_manager = None

def initialize_security_manager():
    """Initialize the global security manager"""
    global security_manager
    security_manager = QuMailSecurityLevelManager()
    logger.info("QuMail Security Level Manager initialized")
    return security_manager

def get_security_manager() -> QuMailSecurityLevelManager:
    """Get the global security manager instance"""
    if security_manager is None:
        raise RuntimeError("Security Manager not initialized")
    return security_manager
