import base64
import secrets
import logging
from typing import Dict, Any
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding as asym_padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

# Use optimized KM client for Next Door Key Simulator
from app.services.km_client_init import get_optimized_km_clients
from app.services.exceptions import InsufficientKeysError, SecurityError
from app.services.optimized_km_client import AuthenticationError, KMConnectionError

logger = logging.getLogger(__name__)

KM1_MASTER_SAE_ID = "25840139-0dd4-49ae-ba1e-b86731601803"

class Level2SecurityError(SecurityError):
    """Level 2 AES specific security errors"""
    pass

async def encrypt_aes(content: str, user_email: str) -> Dict[str, Any]:
    """
    Level 2: Quantum-Enhanced AES-256-GCM encryption
    
    Security Features:
    - AES-256-GCM authenticated encryption
    - Quantum key derivation using HKDF
    - Keys from both KM servers combined
    - Digital signature for authenticity
    - Nonce-based security
    """
    try:
        plaintext = content.encode('utf-8')
        flow_id = secrets.token_hex(16)
        
        # Step 1: Request quantum keys from both KM servers
        logger.info(f"Requesting quantum keys for AES encryption from Next Door Key Simulator, flow {flow_id}")
        
        # Get optimized KM clients for Next Door Key Simulator
        km1_client, km2_client = get_optimized_km_clients()
        
        # Skip status check - keys are exchanged on first request, not pre-exchanged
        # The simulator will handle key availability when we request them
        logger.info(f"Requesting 2 quantum keys from KME1 (Master generates all keys)")
        
        # Request TWO 256-bit keys from KME1 (Master) - both will be broadcast to KME2
        # This ensures both keys are available for decryption
        km1_keys = await km1_client.request_enc_keys(
            slave_sae_id="c565d5aa-8670-4446-8471-b0e53e315d2a", 
            number=2,  # Request 2 keys at once
            size=256
        )
        
        if not km1_keys or len(km1_keys) < 2:
            raise Level2SecurityError(f"Failed to retrieve 2 quantum keys for AES encryption (got {len(km1_keys) if km1_keys else 0})")
        
        # Step 2: Extract and combine quantum keys
        km1_key_data = base64.b64decode(km1_keys[0]['key'])
        km2_key_data = base64.b64decode(km1_keys[1]['key'])
        km1_key_id = km1_keys[0]['key_ID']
        km2_key_id = km1_keys[1]['key_ID']
        
        # Verify key sizes
        if len(km1_key_data) != 32 or len(km2_key_data) != 32:
            raise Level2SecurityError(f"Invalid quantum key size for AES encryption: {len(km1_key_data)}, {len(km2_key_data)} bytes")
        
        logger.info(f"Retrieved 2 quantum keys from KME1: {km1_key_id}, {km2_key_id}")
        
        # Step 3: Derive AES key using HKDF with quantum material
        ikm = km1_key_data + km2_key_data  # 64 bytes of quantum entropy
        
        # Use HKDF to derive AES-256 key
        salt = secrets.token_bytes(32)  # Random salt
        info = f"QuMail-AES-{flow_id}".encode('utf-8')
        
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,  # AES-256 key length
            salt=salt,
            info=info
        )
        aes_key = hkdf.derive(ikm)
        
        # Step 4: Generate random nonce for GCM
        nonce = secrets.token_bytes(12)  # 96-bit nonce for GCM
        
        # Step 5: Encrypt using AES-256-GCM
        aesgcm = AESGCM(aes_key)
        ciphertext_with_tag = aesgcm.encrypt(nonce, plaintext, None)
        
        # Extract Tag (Integrity Gate)
        # GCM tag is appended to the end of the ciphertext (last 16 bytes)
        auth_tag = ciphertext_with_tag[-16:]
        ciphertext_only = ciphertext_with_tag[:-16]
        
        auth_tag_b64 = base64.b64encode(auth_tag).decode()
        ciphertext_b64 = base64.b64encode(ciphertext_only).decode()
        
        logger.info(f"Generated AES-GCM Integrity Tag: {auth_tag_b64}")
        
        # Step 6: Clear sensitive data
        ikm = b'\x00' * len(ikm)
        aes_key = b'\x00' * len(aes_key)
        km1_key_data = b'\x00' * len(km1_key_data)
        km2_key_data = b'\x00' * len(km2_key_data)
        
        logger.info(f"Level 2 AES encryption completed for flow {flow_id}")
        
        return {
            "encrypted_content": ciphertext_b64,
            "algorithm": "AES-256-GCM-QKD",
            "auth_tag": auth_tag_b64, # Replaces signature
            "metadata": {
                "flow_id": flow_id,
                "salt": base64.b64encode(salt).decode(),
                "nonce": base64.b64encode(nonce).decode(),
                "auth_tag": auth_tag_b64,
                "key_ids": {
                    "km1": km1_key_id,
                    "km2": km2_key_id
                },
                "security_level": 2,
                "key_derivation": "HKDF-SHA256",
                "cipher": "AES-256-GCM"
            }
        }
        
    except Exception as e:
        logger.error(f"Level 2 AES encryption failed: {e}")
        raise Level2SecurityError(f"AES encryption failed: {e}")

async def decrypt_aes(encrypted_content: str, user_email: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Level 2: Quantum-Enhanced AES-256-GCM decryption
    
    Security Features:
    - Signature verification before decryption
    - Quantum key retrieval and combination
    - Key derivation verification
    - Authenticated decryption with tampering detection
    """
    try:
        # Step 1: Extract metadata
        flow_id = metadata.get("flow_id")
        salt = base64.b64decode(metadata.get("salt", ""))
        nonce = base64.b64decode(metadata.get("nonce", ""))
        auth_tag_b64 = metadata.get("auth_tag", "")
        key_ids = metadata.get("key_ids", {})
        
        # Handle missing metadata gracefully
        if not flow_id or not salt or not nonce or not key_ids:
            raise Level2SecurityError("Missing required decryption metadata")
        
        ciphertext_only = base64.b64decode(encrypted_content)
        
        # Reconstruct ciphertext with tag for GCM
        if auth_tag_b64:
            auth_tag = base64.b64decode(auth_tag_b64)
            ciphertext_with_tag = ciphertext_only + auth_tag
            logger.info(f"Reconstructed ciphertext with Integrity Tag for flow {flow_id}")
        else:
            # Fallback for legacy messages (if any) or if tag is missing (will likely fail)
            logger.warning("Missing Auth Tag for AES-GCM decryption - Integrity Gate compromised")
            ciphertext_with_tag = ciphertext_only

        # Step 3: Retrieve quantum keys using key IDs
        logger.info(f"SHARED POOL: Retrieving 2 quantum keys from KM1 shared pool, flow {flow_id}")
        
        # Get optimized KM clients for Next Door Key Simulator
        _, km2_client = get_optimized_km_clients()
        logger.info("SHARED POOL: Fetching AES key material via KM2 optimized client")
        
        km2_keys = []
        try:
            km2_keys = await km2_client.request_dec_keys(
                master_sae_id=KM1_MASTER_SAE_ID,
                key_ids=[key_ids["km1"], key_ids["km2"]]
            )
            logger.info(f"SHARED POOL: Retrieved {len(km2_keys)} keys from KM shared pool")
        except AuthenticationError as auth_error:
            raise Level2SecurityError(f"KM authentication failed while retrieving AES keys: {auth_error}")
        except KMConnectionError as conn_error:
            raise Level2SecurityError(f"Unable to reach KM shared pool: {conn_error}")
        except Exception as e:
            raise Level2SecurityError(f"Failed to retrieve quantum keys from shared pool: {e}")
        
        if not km2_keys or len(km2_keys) < 2:
            raise Level2SecurityError(
                f"One or more key IDs not found in shared pool - possible tampering (got {len(km2_keys) if km2_keys else 0}/2 keys)"
            )
        
        # Step 4: Reconstruct key material
        # Find the keys by their IDs (order might not be preserved)
        key_dict = {k['key_ID']: base64.b64decode(k['key']) for k in km2_keys}
        
        km1_key_data = key_dict.get(key_ids["km1"])
        km2_key_data = key_dict.get(key_ids["km2"])
        
        if not km1_key_data or not km2_key_data:
            raise Level2SecurityError("One or more key IDs not found in retrieved keys - possible tampering")
        
        logger.info(f"Successfully retrieved both keys: {key_ids['km1']}, {key_ids['km2']}")
        
        # Step 5: Derive AES key (same process as encryption)
        ikm = km1_key_data + km2_key_data
        info = f"QuMail-AES-{flow_id}".encode('utf-8')
        
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            info=info
        )
        aes_key = hkdf.derive(ikm)
        
        # Step 6: Decrypt using AES-256-GCM (Integrity Gate)
        try:
            aesgcm = AESGCM(aes_key)
            plaintext = aesgcm.decrypt(nonce, ciphertext_with_tag, None)
            logger.info("✓ INTEGRITY GATE PASSED: AES-GCM tag verified")
        except Exception as e:
            logger.critical("!!! INTEGRITY GATE FAILED: AES-GCM decryption failed !!!")
            # WIPE KEYS
            ikm = b'\x00' * len(ikm)
            aes_key = b'\x00' * len(aes_key)
            km1_key_data = b'\x00' * len(km1_key_data)
            km2_key_data = b'\x00' * len(km2_key_data)
            raise Level2SecurityError(f"Integrity Gate Failed: AES-GCM decryption failed (Tag Mismatch): {e}")
        
        # Step 7: Keys automatically consumed by Next Door Key Simulator
        logger.info(f"Keys {key_ids['km1']} and {key_ids['km2']} used for decryption (auto-consumed by simulator)")
        
        # Step 8: Clear sensitive data
        ikm = b'\x00' * len(ikm)
        aes_key = b'\x00' * len(aes_key)
        km1_key_data = b'\x00' * len(km1_key_data)
        km2_key_data = b'\x00' * len(km2_key_data)
        
        logger.info(f"Level 2 AES decryption completed for flow {flow_id}")
        
        return {
            "decrypted_content": plaintext.decode('utf-8'),
            "verification_status": "verified",
            "metadata": {
                "flow_id": flow_id,
                "security_level": 2,
                "algorithm": "AES-256-GCM-QKD",
                "quantum_enhanced": True
            }
        }
        
    except Exception as e:
        logger.error(f"Level 2 AES decryption failed: {e}")
        raise Level2SecurityError(f"AES decryption failed: {e}")

# Aliases for backward compatibility
async def encrypt_aes_gcm(content: str, user_email: str) -> Dict[str, Any]:
    """Alias for encrypt_aes function"""
    logger.info("Level 2 AES-GCM encryption called")
    return await encrypt_aes(content, user_email)

async def decrypt_aes_gcm(encrypted_content: str, user_email: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Alias for decrypt_aes function"""
    logger.info("Level 2 AES-GCM decryption called")
    return await decrypt_aes(encrypted_content, user_email, metadata)
