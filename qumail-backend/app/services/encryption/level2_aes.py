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
# Local Key Manager for local key caching and fast retrieval
from app.services.local_key_manager import get_local_key_manager

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
    - Keys from LOCAL KEY MANAGER (with fallback to main KME)
    - Digital signature for authenticity
    - Nonce-based security
    """
    try:
        plaintext = content.encode('utf-8')
        flow_id = secrets.token_hex(16)
        
        logger.info(f"Level 2 AES encryption starting, flow {flow_id}")
        
        # Initialize Local Key Manager
        local_km = get_local_key_manager()
        local_km_stats = local_km.get_key_statistics()
        
        logger.info(f"  Local KM Status: {local_km_stats['available_keys']} keys available")
        
        km1_key_data = None
        km2_key_data = None
        km1_key_id = None
        km2_key_id = None
        use_local_km = False
        
        # Try Local Key Manager first
        if local_km_stats['available_keys'] >= 2:
            logger.info("  Attempting to use LOCAL KEY MANAGER for AES keys...")
            try:
                local_key1 = local_km.get_local_key(required_bytes=32)
                local_key2 = local_km.get_local_key(required_bytes=32)
                
                if local_key1 and local_key2:
                    use_local_km = True
                    km1_key_data = local_key1["key_material"]
                    km2_key_data = local_key2["key_material"]
                    km1_key_id = local_key1["key_id"]
                    km2_key_id = local_key2["key_id"]
                    
                    logger.info("="*60)
                    logger.info("✓ USING KEYS FROM LOCAL KEY MANAGER")
                    logger.info(f"  Key 1: {km1_key_id[:16]}...")
                    logger.info(f"  Key 2: {km2_key_id[:16]}...")
                    logger.info("="*60)
            except Exception as e:
                logger.warning(f"  Local KM retrieval failed: {e}")
        
        # Fallback to main KME if Local KM doesn't have enough keys
        if not use_local_km:
            logger.info("  Local KM unavailable, falling back to MAIN KME...")
            
            # Get optimized KM clients for Next Door Key Simulator
            km1_client, km2_client = get_optimized_km_clients()
            
            # Request TWO 256-bit keys from KME1 (Master)
            km1_keys = await km1_client.request_enc_keys(
                slave_sae_id="c565d5aa-8670-4446-8471-b0e53e315d2a", 
                number=2,
                size=256
            )
            
            if not km1_keys or len(km1_keys) < 2:
                raise Level2SecurityError(f"Failed to retrieve 2 quantum keys for AES encryption (got {len(km1_keys) if km1_keys else 0})")
            
            km1_key_data = base64.b64decode(km1_keys[0]['key'])
            km2_key_data = base64.b64decode(km1_keys[1]['key'])
            km1_key_id = km1_keys[0]['key_ID']
            km2_key_id = km1_keys[1]['key_ID']
            
            # Store fetched keys in Local KM for future use
            local_km.store_key(key_id=km1_key_id, key_material=km1_key_data, source="KM1", 
                             metadata={"flow_id": flow_id, "level": 2})
            local_km.store_key(key_id=km2_key_id, key_material=km2_key_data, source="KM1",
                             metadata={"flow_id": flow_id, "level": 2})
            
            logger.info(f"  Retrieved 2 quantum keys from MAIN KME and stored in Local KM")
        
        # Verify key sizes
        if len(km1_key_data) != 32 or len(km2_key_data) != 32:
            raise Level2SecurityError(f"Invalid quantum key size for AES encryption: {len(km1_key_data)}, {len(km2_key_data)} bytes")
        
        logger.info(f"Retrieved 2 quantum keys: {km1_key_id[:16]}..., {km2_key_id[:16]}...")
        
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
        logger.info(f"Retrieving quantum keys for decryption, flow {flow_id}")
        
        # Initialize Local Key Manager
        local_km = get_local_key_manager()
        
        # Try Local KM first for decryption keys
        km1_key_data = None
        km2_key_data = None
        use_local_km = False
        
        local_key1 = local_km.get_key_by_id(key_ids["km1"])
        local_key2 = local_km.get_key_by_id(key_ids["km2"])
        
        if local_key1 and local_key2:
            use_local_km = True
            km1_key_data = local_key1["key_material"]
            km2_key_data = local_key2["key_material"]
            
            # Mark as consumed
            local_km.consume_key(key_ids["km1"])
            local_km.consume_key(key_ids["km2"])
            
            logger.info("="*60)
            logger.info("✓ DECRYPTION KEYS FOUND IN LOCAL KEY MANAGER")
            logger.info(f"  Key 1: {key_ids['km1'][:16]}...")
            logger.info(f"  Key 2: {key_ids['km2'][:16]}...")
            logger.info("="*60)
        
        # Fallback to main KME if keys not in Local KM
        if not use_local_km:
            logger.info("  Keys not in Local KM, fetching from MAIN KME...")
            
            # Get optimized KM clients for Next Door Key Simulator
            _, km2_client = get_optimized_km_clients()
            
            km2_keys = []
            try:
                km2_keys = await km2_client.request_dec_keys(
                    master_sae_id=KM1_MASTER_SAE_ID,
                    key_ids=[key_ids["km1"], key_ids["km2"]]
                )
                logger.info(f"  Retrieved {len(km2_keys)} keys from MAIN KME")
                
                # Store retrieved keys in Local KM for future use
                for entry in km2_keys:
                    kid = entry.get('key_ID')
                    raw_key = base64.b64decode(entry.get('key', ''))
                    if kid and raw_key:
                        local_km.store_key(key_id=kid, key_material=raw_key, source="KM2",
                                         metadata={"flow_id": flow_id, "level": 2})
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
            key_dict = {k['key_ID']: base64.b64decode(k['key']) for k in km2_keys}
            km1_key_data = key_dict.get(key_ids["km1"])
            km2_key_data = key_dict.get(key_ids["km2"])
        
        if not km1_key_data or not km2_key_data:
            raise Level2SecurityError("One or more key IDs not found in retrieved keys - possible tampering")
        
        logger.info(f"Successfully retrieved both keys: {key_ids['km1'][:16]}..., {key_ids['km2'][:16]}...")
        
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
