import logging
import secrets
import base64
from typing import Dict, Any
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding as asym_padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidSignature

try:
    # Try relative imports first (works at runtime)
    from ..km_client_init import get_optimized_km_clients
    from ..exceptions import Level4SecurityError, InsufficientKeysError
    from ..local_private_key_store import local_private_key_store
except ImportError:
    # Fall back to absolute imports (helps Pylance/IDE)
    from app.services.km_client_init import get_optimized_km_clients
    from app.services.exceptions import Level4SecurityError, InsufficientKeysError
    from app.services.local_private_key_store import local_private_key_store

logger = logging.getLogger(__name__)

async def encrypt_rsa(content: str, user_email: str) -> Dict[str, Any]:
    """Level 4: RSA-4096 + AES-256-GCM hybrid encryption with quantum enhancement"""
    try:
        plaintext = content.encode("utf-8")
        flow_id = secrets.token_hex(16)
        
        # Generate RSA-4096 key pair
        rsa_private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=4096, backend=default_backend()
        )
        rsa_public_key = rsa_private_key.public_key()
        
        # Generate session AES key (standard cryptographically secure random)
        session_key = secrets.token_bytes(32)
        quantum_enhanced = False
        
        # Level 4 uses standard RSA-4096 encryption (like Gmail) without quantum enhancement
        
        # Encrypt session key with RSA
        encrypted_session_key = rsa_public_key.encrypt(
            session_key, asym_padding.OAEP(
                mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(), label=None
            )
        )
        
        # Encrypt content with AES-GCM
        iv = secrets.token_bytes(12)
        cipher = Cipher(algorithms.AES(session_key), modes.GCM(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        
        aad = f"Level4-RSA-{flow_id}-{user_email}".encode()
        encryptor.authenticate_additional_data(aad)
        ciphertext_bytes = encryptor.update(plaintext) + encryptor.finalize()
        auth_tag = encryptor.tag
        
        # Generate RSA Signature (Normal Signature)
        # Sign the ciphertext to ensure integrity and authenticity
        signature = rsa_private_key.sign(
            ciphertext_bytes,
            asym_padding.PSS(
                mgf=asym_padding.MGF1(hashes.SHA256()),
                salt_length=asym_padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        signature_b64 = base64.b64encode(signature).decode()
        logger.info(f"Generated RSA-4096 Signature for flow {flow_id}")

        public_key_pem = rsa_public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        # Persist private key locally (only public key goes to Mongo)
        private_key_pem = rsa_private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

        private_key_ref = flow_id
        try:
            local_private_key_store.save_private_keys(
                private_key_ref,
                4,
                {"rsa_private_key": base64.b64encode(private_key_pem).decode()},
            )
            logger.info(f"Stored Level 4 private key locally (ref: {private_key_ref})")
        except Exception as e:
            logger.warning(f"Failed to store Level 4 private key locally: {e}")
        
        return {
            "encrypted_content": base64.b64encode(ciphertext_bytes).decode(),
            "algorithm": "RSA-4096-AES-256-GCM",
            "signature": signature_b64,
            "auth_tag": base64.b64encode(auth_tag).decode(),
            "metadata": {
                "flow_id": flow_id,
                "public_key": base64.b64encode(public_key_pem).decode(),
                "encrypted_session_key": base64.b64encode(encrypted_session_key).decode(),
                "iv": base64.b64encode(iv).decode(),
                "auth_tag": base64.b64encode(auth_tag).decode(),
                "signature": signature_b64,
                "aad": base64.b64encode(aad).decode(),
                "security_level": 4,
                "quantum_enhanced": quantum_enhanced,
                "private_key_ref": private_key_ref,
            }
        }
        
    except Exception as e:
        logger.error(f"Level 4 RSA encryption failed: {e}")
        raise Level4SecurityError(f"RSA encryption failed: {e}")

async def decrypt_rsa(encrypted_content: str, user_email: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Level 4: RSA-4096 + AES-256-GCM hybrid decryption"""
    try:
        flow_id = metadata.get("flow_id")
        ciphertext = base64.b64decode(encrypted_content)
        encrypted_session_key = base64.b64decode(metadata.get("encrypted_session_key"))
        iv = base64.b64decode(metadata.get("iv"))
        auth_tag = base64.b64decode(metadata.get("auth_tag"))
        aad = base64.b64decode(metadata.get("aad"))
        signature_b64 = metadata.get("signature")

        private_key_ref = metadata.get("private_key_ref") or flow_id

        # Load stored private key for decryption
        stored_private = None
        try:
            stored_private = local_private_key_store.get_private_keys(private_key_ref)
        except Exception as e:
            logger.warning(f"Failed to load Level 4 private key locally: {e}")

        private_key_b64 = metadata.get("private_key")
        if not private_key_b64 and stored_private:
            private_key_b64 = stored_private.get("rsa_private_key")

        if not private_key_b64:
            raise Level4SecurityError("Private key not found locally for Level 4 decryption")

        private_key_pem = base64.b64decode(private_key_b64)
        rsa_private_key = serialization.load_pem_private_key(
            private_key_pem,
            password=None,
            backend=default_backend()
        )

        # Backfill local store for legacy metadata that carried the private key
        if stored_private is None:
            try:
                local_private_key_store.save_private_keys(
                    private_key_ref,
                    4,
                    {"rsa_private_key": private_key_b64},
                )
            except Exception as e:
                logger.warning(f"Failed to backfill Level 4 private key locally: {e}")
        
        # Verify RSA Signature if present
        if signature_b64:
            try:
                signature = base64.b64decode(signature_b64)
                rsa_public_key = rsa_private_key.public_key()
                rsa_public_key.verify(
                    signature,
                    ciphertext,
                    asym_padding.PSS(
                        mgf=asym_padding.MGF1(hashes.SHA256()),
                        salt_length=asym_padding.PSS.MAX_LENGTH
                    ),
                    hashes.SHA256()
                )
                logger.info(f"✓ RSA SIGNATURE VERIFIED for flow {flow_id}")
            except InvalidSignature:
                logger.critical(f"!!! RSA SIGNATURE VERIFICATION FAILED for flow {flow_id} !!!")
                raise Level4SecurityError("RSA Signature Verification Failed - data integrity compromised")
            except Exception as e:
                logger.warning(f"RSA signature verification error: {e}")
        else:
            logger.warning(f"No RSA signature found for flow {flow_id}")

        # Decrypt session key
        session_key = rsa_private_key.decrypt(
            encrypted_session_key, asym_padding.OAEP(
                mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(), label=None
            )
        )
        
        # Decrypt content (Integrity Gate via GCM)
        cipher = Cipher(algorithms.AES(session_key), modes.GCM(iv, auth_tag), backend=default_backend())
        decryptor = cipher.decryptor()
        decryptor.authenticate_additional_data(aad)
        
        try:
            plaintext = (decryptor.update(ciphertext) + decryptor.finalize()).decode("utf-8")
            logger.info(f"✓ INTEGRITY GATE PASSED: RSA-AES-GCM tag verified for flow {flow_id}")
        except Exception as e:
            logger.critical(f"!!! INTEGRITY GATE FAILED: RSA-AES-GCM decryption failed for flow {flow_id}: {e}")
            raise Level4SecurityError("Integrity Gate Failed: RSA-AES-GCM decryption failed - data corrupted or tampered")
        
        return {
            "decrypted_content": plaintext,
            "verification_status": "verified",
            "metadata": {
                "flow_id": flow_id,
                "security_level": 4,
                "algorithm": "RSA-4096-AES-256-GCM",
                "quantum_enhanced": metadata.get("quantum_enhanced", False)
            }
        }
        
    except Exception as e:
        logger.error(f"Level 4 RSA decryption failed: {e}")
        raise Level4SecurityError(f"RSA decryption failed: {e}")

# Aliases for backward compatibility
async def encrypt_rsa_hybrid(content: str, user_email: str) -> Dict[str, Any]:
    """Alias for encrypt_rsa function"""
    logger.info("Level 4 RSA-Hybrid encryption called")
    return await encrypt_rsa(content, user_email)

async def decrypt_rsa_hybrid(encrypted_content: str, user_email: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Alias for decrypt_rsa function"""
    logger.info("Level 4 RSA-Hybrid decryption called")
    return await decrypt_rsa(encrypted_content, user_email, metadata)
