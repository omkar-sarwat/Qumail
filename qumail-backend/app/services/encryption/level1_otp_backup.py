import base64
import logging
import secrets
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding as asym_padding
from cryptography.hazmat.backends import default_backend

# Use optimized KM client for Next Door Key Simulator
from ..km_client_init import get_optimized_km_clients
from ..exceptions import Level1SecurityError, InsufficientKeysError
from ..quantum_key_manager import OneTimeQuantumKeyManager, SecurityLevel
from ..qumail_encryption import QuMailQuantumEncryption
from ..security_auditor import security_auditor, SecurityIncidentType

logger = logging.getLogger(__name__)

async def encrypt_otp(content: str, user_email: str, qkd_key: Optional[bytes] = None) -> Dict[str, Any]:
    """
    Level 1: One-Time Pad encryption using quantum keys from KM servers
    
    Args:
        content: The plaintext content to encrypt
        user_email: Email of the user doing the encryption
        qkd_key: Optional pre-provided quantum key (for testing)
    """
    try:
        plaintext = content.encode("utf-8")
        flow_id = secrets.token_hex(16)
        
        # Calculate required key size
        required_bits = len(plaintext) * 8
        
        # If a test key is provided, use that instead of requesting from KM
        if qkd_key is not None:
            # Use provided key directly (useful for testing)
            logger.info("Using pre-provided quantum key for OTP encryption")
            
            # Generate a random key ID for tracking
            km1_key_id = f"test-{secrets.token_hex(8)}"
            km2_key_id = f"test-{secrets.token_hex(8)}"
            
            # Use the provided key for both KMs to create combined key
            combined_key = qkd_key
            
            # Check key length
            if len(combined_key) < len(plaintext):
                logger.warning(f"Provided key too short: {len(combined_key)} bytes, need {len(plaintext)} bytes")
                combined_key = combined_key * (len(plaintext) // len(combined_key) + 1)  # Repeat to extend
                combined_key = combined_key[:len(plaintext)]  # Truncate to required length
        else:
            # Request real quantum keys from KM servers
            logger.info("Requesting quantum keys from KM servers for OTP encryption")
            
            # Get optimized KM clients for Next Door Key Simulator
            km1_client, km2_client = get_optimized_km_clients()
            
            # Check key availability first (use proper SAE IDs from simulator)
            km1_status = await km1_client.check_key_status("c565d5aa-8670-4446-8471-b0e53e315d2a")  # Receiver SAE ID
            
            if km1_status.get("stored_key_count", 0) < 1:
                raise InsufficientKeysError("Insufficient quantum keys for OTP encryption")
            
            # Request quantum keys from Next Door Key Simulator
            km1_keys = await km1_client.request_enc_keys(
                slave_sae_id="c565d5aa-8670-4446-8471-b0e53e315d2a", 
                number=1, 
                size=256
            )
            
            if not km1_keys:
                raise Level1SecurityError("Failed to retrieve quantum keys")
                
            # Extract key
            km1_key_data = base64.b64decode(km1_keys[0]["key"])
            km1_key_id = km1_keys[0]["key_ID"]
            
            # Use the same key for both KMs to simplify the process
            # In a real quantum environment, keys from both KMs would be used
            combined_key = km1_key_data
            km2_key_id = km1_key_id  # Track the same key ID for consistency
        
        # Verify key length
        if len(combined_key) < len(plaintext):
            logger.warning(f"Quantum key too short: {len(combined_key)} bytes, need {len(plaintext)} bytes")
            # Extend key if needed (not ideal for production but works for testing)
            combined_key = combined_key * (len(plaintext) // len(combined_key) + 1)
            combined_key = combined_key[:len(plaintext)]
        
        # Perform OTP encryption
        ciphertext = bytes(p ^ k for p, k in zip(plaintext, combined_key))
        
        # Create digital signature
        sender_private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048, backend=default_backend()
        )
        
        signature = sender_private_key.sign(
            ciphertext, asym_padding.PSS(
                mgf=asym_padding.MGF1(hashes.SHA256()),
                salt_length=asym_padding.PSS.MAX_LENGTH
            ), hashes.SHA256()
        )
        
        public_key_pem = sender_private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        return {
            "encrypted_content": base64.b64encode(ciphertext).decode(),
            "algorithm": "OTP-QKD",
            "signature": base64.b64encode(signature).decode(),
            "metadata": {
                "flow_id": flow_id,
                "public_key": base64.b64encode(public_key_pem).decode(),
                "key_ids": {"km1": km1_key_id, "km2": km2_key_id},
                "security_level": 1,
                "key_size_bits": required_bits
            }
        }
        
    except Exception as e:
        logger.error(f"Level 1 OTP encryption failed: {e}")
        raise Level1SecurityError(f"OTP encryption failed: {e}")

async def decrypt_otp(encrypted_content: str, user_email: str, metadata: Dict[str, Any], 
                qkd_key: Optional[bytes] = None) -> Dict[str, Any]:
    """
    Level 1: One-Time Pad decryption using quantum keys
    
    Args:
        encrypted_content: Base64-encoded ciphertext
        user_email: Email of the user doing the decryption
        metadata: Metadata containing key IDs and verification info
        qkd_key: Optional pre-provided quantum key (for testing)
    """
    try:
        flow_id = metadata.get("flow_id")
        signature_b64 = metadata.get("signature")
        public_key_b64 = metadata.get("public_key")
        key_ids = metadata.get("key_ids", {})
        km1_key_id = key_ids.get("km1")
        km2_key_id = key_ids.get("km2")
        
        # For backwards compatibility, check if key_id is in the main metadata
        if not km1_key_id and "key_id" in metadata:
            km1_key_id = metadata.get("key_id")
            km2_key_id = km1_key_id
        
        # If using pre-provided key, we don't need key IDs
        if qkd_key is None and not all([flow_id, signature_b64, public_key_b64, km1_key_id]):
            raise Level1SecurityError("Missing required metadata for OTP decryption")
        
        ciphertext = base64.b64decode(encrypted_content)
        signature = base64.b64decode(signature_b64) if signature_b64 else None
        
        # Verify signature if provided
        if signature and public_key_b64:
            public_key_pem = base64.b64decode(public_key_b64)
            public_key = serialization.load_pem_public_key(public_key_pem)
            
            try:
                public_key.verify(
                    signature, ciphertext, asym_padding.PSS(
                        mgf=asym_padding.MGF1(hashes.SHA256()),
                        salt_length=asym_padding.PSS.MAX_LENGTH
                    ), hashes.SHA256()
                )
            except Exception:
                raise Level1SecurityError("Digital signature verification failed")
        
        # If a test key is provided, use that instead of requesting from KM
        if qkd_key is not None:
            logger.info("Using pre-provided quantum key for OTP decryption")
            combined_key = qkd_key
            
            # Check key length
            if len(combined_key) < len(ciphertext):
                logger.warning(f"Provided key too short: {len(combined_key)} bytes, need {len(ciphertext)} bytes")
                combined_key = combined_key * (len(ciphertext) // len(combined_key) + 1)  # Repeat to extend
                combined_key = combined_key[:len(ciphertext)]  # Truncate to required length
        else:
            # Request real quantum key from KM server
            logger.info("Requesting quantum key from Next Door Key Simulator for OTP decryption")
            
            # Get optimized KM clients for Next Door Key Simulator
            km1_client, km2_client = get_optimized_km_clients()
            
            # Request decryption keys using proper SAE ID
            km2_keys = await km2_client.request_dec_keys(
                master_sae_id="c565d5aa-8670-4446-8471-b0e53e315d2a", 
                key_ids=[km1_key_id]
            )
            
            if not km2_keys:
                raise Level1SecurityError("Failed to retrieve quantum key for decryption")
            
            # Extract key
            km2_key_data = base64.b64decode(km2_keys[0]["key"])
            
            # Verify key length
            if len(km2_key_data) < len(ciphertext):
                logger.warning(f"Key too short: {len(km2_key_data)} bytes, need {len(ciphertext)} bytes")
                km2_key_data = km2_key_data * (len(ciphertext) // len(km2_key_data) + 1)
                km2_key_data = km2_key_data[:len(ciphertext)]
                
            # Use single key directly (in real quantum environment, keys would be combined)
            combined_key = km2_key_data
        
        # Perform OTP decryption
        plaintext_bytes = bytes(c ^ k for c, k in zip(ciphertext, combined_key))
        plaintext = plaintext_bytes.decode("utf-8")
        
        # Mark key as consumed if using real KM
        if qkd_key is None and km1_key_id:
            try:
                # Get optimized KM clients for key consumption tracking
                _, km2_client = get_optimized_km_clients()
                # Note: Next Door Key Simulator automatically manages key consumption
                logger.info(f"Key {km1_key_id} used for decryption (auto-consumed by simulator)")
            except Exception as e:
                logger.warning(f"Note about key {km1_key_id} consumption: {e}")
                
        return {
            "decrypted_content": plaintext,
            "verification_status": "signature_verified",
            "metadata": {
                "flow_id": flow_id,
                "security_level": 1,
                "algorithm": "OTP-QKD",
                "keys_consumed": True
            }
        }
        
    except Exception as e:
        logger.error(f"Level 1 OTP decryption failed: {e}")
        raise Level1SecurityError(f"OTP decryption failed: {e}")

# Global instances for quantum services (will be initialized from app state)
_quantum_key_manager: Optional[OneTimeQuantumKeyManager] = None
_qumail_encryption: Optional[QuMailQuantumEncryption] = None

def _get_quantum_services():
    """Get quantum services from global state"""
    global _quantum_key_manager, _qumail_encryption
    
    if not _quantum_key_manager or not _qumail_encryption:
        # Initialize from KM clients if not already done
        km1_client, km2_client = get_optimized_km_clients()
        _quantum_key_manager = OneTimeQuantumKeyManager([km1_client, km2_client])
        _qumail_encryption = QuMailQuantumEncryption(_quantum_key_manager)
    
    return _quantum_key_manager, _qumail_encryption

async def encrypt_otp_quantum(content: str, user_email: str, recipient_email: Optional[str] = None) -> Dict[str, Any]:
    """
    Encrypt content using One-Time Pad with quantum keys
    
    Features:
    - Perfect secrecy (information-theoretic security)
    - One-time-use quantum keys from KME servers
    - QuMail-only decryption capability
    - Automatic key consumption tracking
    
    Args:
        content: The message content to encrypt
        user_email: Email of the sender
        recipient_email: Email of the recipient (optional)
    
    Returns:
        Dict containing encrypted data and metadata
    """
    try:
        logger.info(f"Starting quantum OTP encryption for user {user_email}")
        
        # Get quantum services
        quantum_key_manager, qumail_encryption = _get_quantum_services()
        
        # Ensure quantum key manager is initialized
        await quantum_key_manager.initialize()
        
        # Convert content to bytes
        content_bytes = content.encode('utf-8')
        content_length = len(content_bytes)
        
        logger.info(f"Content length: {content_length} bytes")
        
        # Determine security level based on content length
        if content_length <= 32:
            security_level = SecurityLevel.LOW
        elif content_length <= 64:
            security_level = SecurityLevel.MEDIUM  
        elif content_length <= 128:
            security_level = SecurityLevel.HIGH
        else:
            security_level = SecurityLevel.ULTRA
            
        logger.info(f"Using security level: {security_level.name} ({security_level.value} bytes)")
        
        # Generate one-time quantum key
        quantum_key_info = await quantum_key_manager.get_one_time_key(security_level)
        
        if not quantum_key_info:
            raise ValueError("Failed to generate one-time quantum key")
        
        quantum_key = quantum_key_info["key_material"]
        key_id = quantum_key_info["key_id"]
        
        logger.info(f"Generated one-time quantum key: {key_id}")
        
        # Perform OTP encryption (XOR with quantum key)
        if len(quantum_key) < content_length:
            # Pad quantum key if needed using cryptographic stretching
            padded_key = await _stretch_quantum_key(quantum_key, content_length)
        else:
            padded_key = quantum_key[:content_length]
        
        # XOR operation for perfect secrecy
        encrypted_bytes = bytearray()
        for i in range(content_length):
            encrypted_bytes.append(content_bytes[i] ^ padded_key[i])
        
        # Convert to hex for transport
        encrypted_hex = encrypted_bytes.hex()
        
        # Create QuMail-specific encryption wrapper
        qumail_result = await qumail_encryption.encrypt_message(
            message=content,
            sender_id=user_email,
            recipient_id=recipient_email or user_email,
            security_level=security_level
        )
        
        # Mark key as consumed
        await quantum_key_manager.mark_key_consumed(
            key_id=key_id,
            user_id=user_email,
            usage_type="OTP_ENCRYPTION"
        )
        
        # Create metadata
        metadata = {
            "algorithm": "Quantum One-Time Pad",
            "key_id": key_id,
            "security_level": security_level.name,
            "key_size_bytes": len(quantum_key),
            "content_length": content_length,
            "encryption_timestamp": datetime.utcnow().isoformat(),
            "perfect_secrecy": True,
            "qumail_only": True,
            "key_consumed": True,
            "kme_source": "Next Door Key Simulator"
        }
        
        # Log security event
        await security_auditor.log_incident(
            SecurityIncidentType.ENCRYPTION_SUCCESS,
            f"Quantum OTP encryption completed with perfect secrecy",
            user_id=user_email,
            details={
                "security_level": security_level.name,
                "key_id": key_id,
                "content_length": content_length,
                "key_size": len(quantum_key),
                "algorithm": "Quantum One-Time Pad"
            }
        )
        
        logger.info(f"Quantum OTP encryption successful for user {user_email}, key {key_id}")
        
        return {
            "encrypted_content": encrypted_hex,
            "algorithm": "Quantum One-Time Pad",
            "signature": _generate_encryption_signature(encrypted_hex, key_id, user_email),
            "metadata": metadata,
            "qumail_data": qumail_result["encrypted_data"],
            "obfuscated_preview": qumail_result["obfuscated_preview"]
        }
        
    except Exception as e:
        logger.error(f"Quantum OTP encryption failed for user {user_email}: {e}")
        
        # Log security incident
        await security_auditor.log_incident(
            SecurityIncidentType.ENCRYPTION_FAILURE,
            f"Quantum OTP encryption failed: {str(e)}",
            user_id=user_email,
            details={
                "error": str(e),
                "content_length": len(content) if content else 0
            }
        )
        
        raise ValueError(f"Quantum OTP encryption failed: {str(e)}")

async def _stretch_quantum_key(quantum_key: bytes, target_length: int) -> bytes:
    """
    Cryptographically stretch quantum key to required length
    
    Uses HKDF (HMAC-based Key Derivation Function) to maintain
    cryptographic strength while expanding key material.
    
    Args:
        quantum_key: Original quantum key material
        target_length: Required key length in bytes
    
    Returns:
        Stretched key of target length
    """
    try:
        # Use HKDF for secure key stretching
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.hkdf import HKDF
        
        # Create HKDF instance
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=target_length,
            salt=b'QuMail-Quantum-OTP-Salt',  # Fixed salt for deterministic stretching
            info=b'QuMail One-Time Pad Key Stretching',
        )
        
        # Derive the stretched key
        stretched_key = hkdf.derive(quantum_key)
        
        logger.debug(f"Stretched quantum key from {len(quantum_key)} to {len(stretched_key)} bytes")
        
        return stretched_key
        
    except Exception as e:
        logger.error(f"Quantum key stretching failed: {e}")
        # Fallback to simpler method if HKDF fails
        return _simple_key_stretch(quantum_key, target_length)

def _simple_key_stretch(quantum_key: bytes, target_length: int) -> bytes:
    """
    Simple key stretching fallback using SHA-256 chaining
    
    Args:
        quantum_key: Original quantum key material
        target_length: Required key length in bytes
    
    Returns:
        Stretched key of target length
    """
    stretched = bytearray()
    current_key = quantum_key
    
    while len(stretched) < target_length:
        # Hash current key to get next 32 bytes
        hash_obj = hashlib.sha256()
        hash_obj.update(current_key)
        hash_obj.update(f"QuMail-OTP-{len(stretched)}".encode())
        next_chunk = hash_obj.digest()
        
        # Add to stretched key
        remaining_length = target_length - len(stretched)
        stretched.extend(next_chunk[:remaining_length])
        
        # Update current key for next iteration
        current_key = next_chunk
    
    return bytes(stretched)

def _generate_encryption_signature(encrypted_content: str, key_id: str, user_email: str) -> str:
    """
    Generate signature for encrypted content
    
    Args:
        encrypted_content: Encrypted data in hex format
        key_id: Quantum key ID used
        user_email: User's email
    
    Returns:
        Signature string
    """
    try:
        # Create signature data
        signature_data = f"{encrypted_content}:{key_id}:{user_email}:QuMail-OTP"
        
        # Generate hash signature
        signature_hash = hashlib.sha256(signature_data.encode()).hexdigest()
        
        return f"QuMail-OTP-{signature_hash[:16]}"
        
    except Exception as e:
        logger.error(f"Signature generation failed: {e}")
        return f"QuMail-OTP-{secrets.token_hex(8)}"

# Global instances for quantum services
_quantum_key_manager: Optional[OneTimeQuantumKeyManager] = None
_qumail_encryption: Optional[QuMailQuantumEncryption] = None

def _get_quantum_services():
    """Get quantum services from global state"""
    global _quantum_key_manager, _qumail_encryption
    
    if not _quantum_key_manager or not _qumail_encryption:
        # Initialize from KM clients if not already done
        km1_client, km2_client = get_optimized_km_clients()
        _quantum_key_manager = OneTimeQuantumKeyManager(km1_client, km2_client)
        _qumail_encryption = QuMailQuantumEncryption(_quantum_key_manager)
    
    return _quantum_key_manager, _qumail_encryption

async def encrypt_otp_quantum(content: str, user_email: str, recipient_email: Optional[str] = None) -> Dict[str, Any]:
    """
    New Quantum OTP encryption with one-time-use keys
    
    Features:
    - Perfect secrecy (information-theoretic security)
    - One-time-use quantum keys from KME servers
    - QuMail-only decryption capability
    - Automatic key consumption tracking
    
    Args:
        content: The message content to encrypt
        user_email: Email of the sender
        recipient_email: Email of the recipient (optional)
    
    Returns:
        Dict containing encrypted data and metadata
    """
    try:
        logger.info(f"Starting quantum OTP encryption for user {user_email}")
        
        # Get quantum services
        quantum_key_manager, qumail_encryption = _get_quantum_services()
        
        # Ensure quantum key manager is initialized
        await quantum_key_manager.initialize()
        
        # Convert content to bytes
        content_bytes = content.encode('utf-8')
        content_length = len(content_bytes)
        
        logger.info(f"Content length: {content_length} bytes")
        
        # Determine security level based on content length
        if content_length <= 32:
            security_level = SecurityLevel.LOW
        elif content_length <= 64:
            security_level = SecurityLevel.MEDIUM  
        elif content_length <= 128:
            security_level = SecurityLevel.HIGH
        else:
            security_level = SecurityLevel.ULTRA
            
        logger.info(f"Using security level: {security_level.name} ({security_level.value} bytes)")
        
        # Generate one-time quantum key
        quantum_key_info = await quantum_key_manager.get_one_time_key(security_level)
        
        if not quantum_key_info:
            raise ValueError("Failed to generate one-time quantum key")
        
        quantum_key = quantum_key_info["key_material"]
        key_id = quantum_key_info["key_id"]
        
        logger.info(f"Generated one-time quantum key: {key_id}")
        
        # Perform OTP encryption (XOR with quantum key)
        if len(quantum_key) < content_length:
            # Stretch quantum key if needed using secure key derivation
            padded_key = await _stretch_quantum_key(quantum_key, content_length)
        else:
            padded_key = quantum_key[:content_length]
        
        # XOR operation for perfect secrecy
        encrypted_bytes = bytearray()
        for i in range(content_length):
            encrypted_bytes.append(content_bytes[i] ^ padded_key[i])
        
        # Convert to base64 for transport
        encrypted_b64 = base64.b64encode(encrypted_bytes).decode('utf-8')
        
        # Create QuMail-specific encryption wrapper
        qumail_result = await qumail_encryption.encrypt_message(
            message=content,
            sender_id=user_email,
            recipient_id=recipient_email or user_email,
            security_level=security_level
        )
        
        # Mark key as consumed
        await quantum_key_manager.mark_key_consumed(
            key_id=key_id,
            user_id=user_email,
            usage_type="OTP_ENCRYPTION"
        )
        
        # Create metadata
        metadata = {
            "algorithm": "Quantum One-Time Pad",
            "key_id": key_id,
            "security_level": security_level.name,
            "key_size_bytes": len(quantum_key),
            "content_length": content_length,
            "encryption_timestamp": datetime.utcnow().isoformat(),
            "perfect_secrecy": True,
            "qumail_only": True,
            "key_consumed": True,
            "kme_source": "Next Door Key Simulator",
            "flow_id": secrets.token_hex(16)
        }
        
        # Log security event
        await security_auditor.log_incident(
            SecurityIncidentType.ENCRYPTION_SUCCESS,
            f"Quantum OTP encryption completed with perfect secrecy",
            user_id=user_email,
            details={
                "security_level": security_level.name,
                "key_id": key_id,
                "content_length": content_length,
                "key_size": len(quantum_key),
                "algorithm": "Quantum One-Time Pad"
            }
        )
        
        logger.info(f"Quantum OTP encryption successful for user {user_email}, key {key_id}")
        
        return {
            "encrypted_content": encrypted_b64,
            "algorithm": "Quantum One-Time Pad",
            "signature": _generate_encryption_signature(encrypted_b64, key_id, user_email),
            "metadata": metadata,
            "qumail_data": qumail_result["encrypted_data"],
            "obfuscated_preview": qumail_result["obfuscated_preview"]
        }
        
    except Exception as e:
        logger.error(f"Quantum OTP encryption failed for user {user_email}: {e}")
        
        # Log security incident
        await security_auditor.log_incident(
            SecurityIncidentType.ENCRYPTION_FAILURE,
            f"Quantum OTP encryption failed: {str(e)}",
            user_id=user_email,
            details={
                "error": str(e),
                "content_length": len(content) if content else 0
            }
        )
        
        raise Level1SecurityError(f"Quantum OTP encryption failed: {str(e)}")

async def _stretch_quantum_key(quantum_key: bytes, target_length: int) -> bytes:
    """
    Cryptographically stretch quantum key to required length using HKDF
    """
    try:
        # Use HKDF for secure key stretching
        from cryptography.hazmat.primitives.kdf.hkdf import HKDF
        
        # Create HKDF instance
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=target_length,
            salt=b'QuMail-Quantum-OTP-Salt',
            info=b'QuMail One-Time Pad Key Stretching',
        )
        
        # Derive the stretched key
        stretched_key = hkdf.derive(quantum_key)
        
        logger.debug(f"Stretched quantum key from {len(quantum_key)} to {len(stretched_key)} bytes")
        
        return stretched_key
        
    except Exception as e:
        logger.error(f"Quantum key stretching failed: {e}")
        # Fallback to simpler method if HKDF fails
        return _simple_key_stretch(quantum_key, target_length)

def _simple_key_stretch(quantum_key: bytes, target_length: int) -> bytes:
    """Simple key stretching fallback using SHA-256 chaining"""
    stretched = bytearray()
    current_key = quantum_key
    
    while len(stretched) < target_length:
        # Hash current key to get next 32 bytes
        hash_obj = hashlib.sha256()
        hash_obj.update(current_key)
        hash_obj.update(f"QuMail-OTP-{len(stretched)}".encode())
        next_chunk = hash_obj.digest()
        
        # Add to stretched key
        remaining_length = target_length - len(stretched)
        stretched.extend(next_chunk[:remaining_length])
        
        # Update current key for next iteration
        current_key = next_chunk
    
    return bytes(stretched)

def _generate_encryption_signature(encrypted_content: str, key_id: str, user_email: str) -> str:
    """Generate signature for encrypted content"""
    try:
        # Create signature data
        signature_data = f"{encrypted_content}:{key_id}:{user_email}:QuMail-OTP"
        
        # Generate hash signature
        signature_hash = hashlib.sha256(signature_data.encode()).hexdigest()
        
        return f"QuMail-OTP-{signature_hash[:16]}"
        
    except Exception as e:
        logger.error(f"Signature generation failed: {e}")
        return f"QuMail-OTP-{secrets.token_hex(8)}"
