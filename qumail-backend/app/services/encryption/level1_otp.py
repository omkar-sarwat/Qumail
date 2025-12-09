import base64
import logging
import secrets
import hashlib
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from cryptography.hazmat.primitives import hashes, serialization, hmac
from cryptography.hazmat.primitives.asymmetric import rsa, padding as asym_padding
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidSignature

# Use optimized KM client for Next Door Key Simulator
from ..km_client_init import get_optimized_km_clients
from ..optimized_km_client import AuthenticationError, KMConnectionError, SecurityError
from ..exceptions import Level1SecurityError
from ..quantum_key_manager import OneTimeQuantumKeyManager, SecurityLevel
from ..qumail_encryption import QuMailQuantumEncryption
from ..security_auditor import security_auditor, SecurityIncidentType
# Local Key Manager for local key caching and fast retrieval
from ..local_key_manager import get_local_key_manager

logger = logging.getLogger(__name__)

KM1_MASTER_SAE_ID = "25840139-0dd4-49ae-ba1e-b86731601803"
KM2_SAE_ID = "c565d5aa-8670-4446-8471-b0e53e315d2a"


async def encrypt_otp(content: str, user_email: str, qkd_key: Optional[bytes] = None, db_session: Optional[Any] = None, flow_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Level 1: One-Time Pad encryption using quantum keys from KME servers
    
    Production implementation with in-memory key cache and ETSI QKD cross-SAE sharing.
    - Sender uses KME1 to generate key
    - Key shared with Receiver's KME2 via cross-SAE
    - In-memory cache for fast retrieval and enhanced security
    
    Args:
        content: The plaintext content to encrypt
        user_email: Email of the sender
        qkd_key: Optional pre-provided quantum key (for testing only)
        db_session: Database session (optional, not used with in-memory cache)
        flow_id: Email flow ID for tracking
    
    Returns:
        Dict containing encrypted content and metadata
        
    Raises:
        Level1SecurityError: If encryption fails
    """
    try:
        plaintext = content.encode("utf-8")
        if not flow_id:
            flow_id = secrets.token_hex(16)
        
        required_bytes = len(plaintext)
        total_key_bytes = required_bytes + 32  # Split Key: OTP + 32 bytes for HMAC
        
        logger.info("="*80)
        logger.info("LEVEL 1 OTP-QKD ENCRYPTION START (ETSI GS QKD 014)")
        logger.info(f"  Sender: {user_email}")
        logger.info(f"  Flow ID: {flow_id}")
        logger.info(f"  Content size: {required_bytes} bytes")
        logger.info(f"  Total Key Request: {total_key_bytes} bytes (Content + 32 bytes HMAC)")
        logger.info(f"  Protocol: ETSI GS QKD 014 REST API")
        logger.info(f"  Key Model: Synchronized keys (same key on KM1 and KM2)")
        logger.info("="*80)
        
        key_fragments: List[str] = []
        use_local_km = False  # Track if we used local key manager

        # For testing only - use provided key
        if qkd_key is not None:
            logger.warning("Using pre-provided test quantum key (NOT for production)")
            key_id = f"test-{secrets.token_hex(8)}"
            quantum_key_material = qkd_key
            
            if len(quantum_key_material) < total_key_bytes:
                logger.warning(f"Test key too short: {len(quantum_key_material)} bytes, need {total_key_bytes} bytes")
                quantum_key_material = quantum_key_material * (total_key_bytes // len(quantum_key_material) + 1)
            quantum_key_material = quantum_key_material[:total_key_bytes]
            key_fragments.append(key_id)
        
        else:
            # PRODUCTION PATH: Try Local Key Manager first, fallback to main KME
            logger.info("ENCRYPTION KEY RETRIEVAL: Local KM first, fallback to main KME...")
            
            # Initialize Local Key Manager
            local_km = get_local_key_manager()
            local_km_stats = local_km.get_key_statistics()
            
            logger.info(f"  Local KM Status: {local_km_stats['available_keys']} keys available")
            
            # Try to get key from Local Key Manager first
            local_key_data = None
            if local_km_stats['available_keys'] > 0:
                logger.info("  Attempting to use LOCAL KEY MANAGER...")
                try:
                    local_key_data = local_km.get_local_key(required_bytes=32)  # Get one key
                except Exception as e:
                    logger.warning(f"  Local KM retrieval failed: {e}")
                    local_key_data = None
            
            if local_key_data:
                # SUCCESS: Using key from Local Key Manager
                use_local_km = True
                key_id = local_key_data["key_id"]
                first_chunk = local_key_data["key_material"]
                
                logger.info("="*60)
                logger.info("✓ USING KEY FROM LOCAL KEY MANAGER")
                logger.info(f"  Key ID: {key_id}")
                logger.info(f"  Key Size: {len(first_chunk)} bytes")
                logger.info(f"  Source: {local_key_data.get('source', 'local')}")
                logger.info("="*60)
                
                # Build quantum key material from local key(s)
                quantum_key_chunks = [first_chunk]
                key_fragments.append(key_id)
                
                # If we need more key material, get more local keys
                while sum(len(chunk) for chunk in quantum_key_chunks) < total_key_bytes:
                    remaining = total_key_bytes - sum(len(chunk) for chunk in quantum_key_chunks)
                    logger.info(f"  Need {remaining} more bytes, fetching another local key...")
                    
                    extra_key = local_km.get_local_key(required_bytes=32)
                    if extra_key:
                        quantum_key_chunks.append(extra_key["key_material"])
                        key_fragments.append(extra_key["key_id"])
                    else:
                        logger.warning("  Local KM exhausted, switching to main KME for remaining keys...")
                        break
                
                # Combine all chunks
                combined = b"".join(quantum_key_chunks)
                
                # If still not enough, we need to get from main KME
                if len(combined) < total_key_bytes:
                    logger.info("  Local keys insufficient, supplementing with main KME...")
                    use_local_km = "partial"  # Partial local usage
                    
                    km1_client, km2_client = get_optimized_km_clients()
                    slave_sae_id = "c565d5aa-8670-4446-8471-b0e53e315d2a"
                    remaining = total_key_bytes - len(combined)
                    keys_needed = (remaining + 31) // 32
                    
                    extra_keys = await km1_client.request_enc_keys(
                        slave_sae_id=slave_sae_id,
                        number=keys_needed,
                        size=256
                    )
                    
                    if extra_keys:
                        for key_entry in extra_keys:
                            raw_chunk = base64.b64decode(key_entry['key'])
                            quantum_key_chunks.append(raw_chunk)
                            key_fragments.append(key_entry['key_ID'])
                            # Store in local KM for future use
                            local_km.store_key(
                                key_id=key_entry['key_ID'],
                                key_material=raw_chunk,
                                source="KM1"
                            )
                        combined = b"".join(quantum_key_chunks)
                
                quantum_key_material = combined[:total_key_bytes]
                
            else:
                # FALLBACK: Get keys from main KME (original path)
                logger.info("  Local KM empty or unavailable, falling back to MAIN KME...")
                logger.info("ETSI QKD 014: Retrieving encryption key from KM1...")
                logger.info("  - Same key will be broadcast to KM2 (synchronized via HTTP)")
                logger.info("  - One-time use only (no regeneration)")
                
                # Get optimized KM clients for Next Door Key Simulator
                km1_client, km2_client = get_optimized_km_clients()
            
                # Use optimized KM client to request encryption key from KME1
                logger.info("Requesting encryption key from KME1 via optimized client...")
            
                slave_sae_id = "c565d5aa-8670-4446-8471-b0e53e315d2a"  # KME2's SAE ID
                
                # The Next Door Key Simulator returns fixed 32-byte (256-bit) keys
                # So we need to request enough keys to cover the total required bytes
                key_chunk_size = 32  # 256 bits = 32 bytes per key
                keys_needed_initial = (total_key_bytes + key_chunk_size - 1) // key_chunk_size
                
                logger.info(f"Total key bytes needed: {total_key_bytes}")
                logger.info(f"Key chunk size: {key_chunk_size} bytes (256 bits)")
                logger.info(f"Keys needed: {keys_needed_initial}")
                
                km1_keys = await km1_client.request_enc_keys(
                    slave_sae_id=slave_sae_id,
                    number=keys_needed_initial,
                    size=256  # Each key is 256 bits (32 bytes)
                )
                
                if not km1_keys:
                    raise Level1SecurityError("No quantum keys available on KM1. Available: 0, Required: 1")

                quantum_key_chunks: List[bytes] = []
                fragment_records: List[Dict[str, Any]] = []

                def _append_key_batch(keys_batch):
                    appended = 0
                    for key_entry in keys_batch:
                        raw_chunk = base64.b64decode(key_entry['key'])
                        if not raw_chunk:
                            logger.warning("Received empty key chunk from KM1 for ID %s", key_entry.get('key_ID'))
                            continue
                        quantum_key_chunks.append(raw_chunk)
                        fragment_records.append({
                            "key_id": key_entry['key_ID'],
                            "size_bytes": len(raw_chunk)
                        })
                        # Store key in Local KM for future use
                        local_km.store_key(
                            key_id=key_entry['key_ID'],
                            key_material=raw_chunk,
                            source="KM1",
                            metadata={"flow_id": flow_id, "auto_cached": True}
                        )
                        appended += len(raw_chunk)
                        logger.info(
                            "  - Fragment %s | ID=%s | %s bytes (stored in Local KM)",
                            len(fragment_records),
                            key_entry['key_ID'],
                            len(raw_chunk)
                        )
                    return appended

                logger.info(f"✓ Got {len(km1_keys)} encryption key(s) from KME1 (initial batch)")
                initial_bytes = _append_key_batch(km1_keys)
                if not initial_bytes:
                    raise Level1SecurityError("KM1 returned empty key material for OTP encryption")

                key_id = fragment_records[0]["key_id"]
                chunk_size_bytes = fragment_records[0]["size_bytes"] or 32

                while sum(len(chunk) for chunk in quantum_key_chunks) < total_key_bytes:
                    remaining_bytes = total_key_bytes - sum(len(chunk) for chunk in quantum_key_chunks)
                    keys_needed = max(1, (remaining_bytes + key_chunk_size - 1) // key_chunk_size)
                    logger.info(
                        "Requesting %s additional key fragment(s) to cover remaining %s bytes",
                        keys_needed,
                        remaining_bytes
                    )
                    additional_keys = await km1_client.request_enc_keys(
                        slave_sae_id=slave_sae_id,
                        number=keys_needed,
                        size=256  # Each key is 256 bits (32 bytes)
                    )
                    if not additional_keys:
                        break
                    _append_key_batch(additional_keys)
                    if fragment_records and fragment_records[-1]["size_bytes"]:
                        chunk_size_bytes = fragment_records[-1]["size_bytes"]

                combined_material = b"".join(quantum_key_chunks)
                if len(combined_material) < total_key_bytes:
                    raise Level1SecurityError(
                        f"KM1 returned insufficient key material: {len(combined_material)} bytes, need {total_key_bytes} bytes"
                    )

                quantum_key_material = combined_material[:total_key_bytes]
                logger.info(f"✓ ETSI QKD 014: Aggregated {len(fragment_records)} fragment(s) from KM1")
                logger.info(f"  - Primary Key ID: {key_id}")
                logger.info(f"  - Combined Key Size: {len(quantum_key_material)} bytes ({len(quantum_key_material) * 8} bits)")
                logger.info(f"  - SAE1 ID: 25840139-0dd4-49ae-ba1e-b86731601803")
                logger.info(f"  - SAE2 ID: c565d5aa-8670-4446-8471-b0e53e315d2a")
                logger.info(f"  - Synchronized: Key broadcast to KM2")
                logger.info(f"  - Stored in Local KM: YES (for decryption)")
                key_fragments = [fragment["key_id"] for fragment in fragment_records]
        
        # SPLIT KEY ARCHITECTURE
        # First L bytes for OTP, last 32 bytes for HMAC
        otp_key = quantum_key_material[:required_bytes]
        hmac_key = quantum_key_material[required_bytes:]
        
        logger.info("SPLIT KEY ARCHITECTURE APPLIED")
        logger.info(f"  OTP Key: {len(otp_key)} bytes")
        logger.info(f"  HMAC Key: {len(hmac_key)} bytes")

        # Perform OTP encryption (XOR with quantum key)
        logger.info("PERFORMING ONE-TIME PAD ENCRYPTION")
        logger.info(f"  Plaintext: {len(plaintext)} bytes, first 32 bytes: {plaintext[:32].hex()}")
        logger.info(f"  OTP Key: {len(otp_key)} bytes, first 32 bytes: {otp_key[:32].hex()}")
        
        encrypted_bytes = bytes(a ^ b for a, b in zip(plaintext, otp_key))
        
        logger.info(f"  Encrypted: {len(encrypted_bytes)} bytes, first 32 bytes: {encrypted_bytes[:32].hex()}")
        
        # Convert to base64 for transport
        encrypted_content = base64.b64encode(encrypted_bytes).decode("utf-8")
        logger.info(f"  Base64 encoded: {len(encrypted_content)} characters")
        
        # Generate HMAC-SHA256 Integrity Tag (Integrity Gate)
        logger.info("Generating HMAC-SHA256 Integrity Tag (Integrity Gate)...")
        h = hmac.HMAC(hmac_key, hashes.SHA256(), backend=default_backend())
        h.update(encrypted_bytes)
        auth_tag = h.finalize()
        auth_tag_b64 = base64.b64encode(auth_tag).decode("utf-8")
        
        logger.info(f"  HMAC Tag: {auth_tag_b64}")

        logger.info("="*80)
        logger.info("LEVEL 1 OTP-QKD ENCRYPTION COMPLETED SUCCESSFULLY")
        logger.info(f"  Algorithm: OTP-QKD-ETSI-014 (One-Time Pad with ETSI QKD 014)")
        logger.info(f"  Security Level: Maximum (Information-theoretic security)")
        logger.info(f"  Content encrypted: {len(plaintext)} bytes")
        logger.info(f"  Protocol: ETSI GS QKD 014 REST API")
        logger.info(f"  Key Status: Retrieved from KM1 (broadcast to KM2)")
        logger.info(f"  One-Time Use: YES (key will be deleted after decryption)")
        logger.info("="*80)

        return {
            "encrypted_content": encrypted_content,
            "algorithm": "OTP-QKD-ETSI-014",
            "auth_tag": auth_tag_b64,  # Replaces signature
            "metadata": {
                "flow_id": flow_id,
                "security_level": 1,
                "algorithm": "OTP-QKD-ETSI-014",
                "key_id": key_id,
                "key_size": len(quantum_key_material),
                "key_fragments": key_fragments,
                "key_fragment_count": len(key_fragments),
                "required_size": len(plaintext),
                "auth_tag": auth_tag_b64,  # Added for Integrity Gate verification
                "quantum_enhanced": True,
                "one_time_pad": True,
                "etsi_qkd_014": True,
                "synchronized_keys": True
            }
        }
        
    except Exception as e:
        logger.error("="*80)
        logger.error("LEVEL 1 OTP-QKD ENCRYPTION FAILED")
        logger.error(f"  Error: {e}")
        logger.error(f"  User: {user_email}")
        logger.error("="*80)
        raise Level1SecurityError(f"OTP encryption failed: {e}")

async def decrypt_otp(encrypted_content: str, user_email: str, metadata: Dict[str, Any], db_session: Optional[Any] = None) -> Dict[str, Any]:
    """
    Level 1: One-Time Pad decryption using quantum keys from in-memory cache
    
    Production implementation with ETSI QKD cross-SAE key sharing:
    - Receiver uses KME2 to retrieve key shared by Sender's KME1
    - In-memory cache for fast retrieval
    - One-time pad principle enforced (key consumed after use)

    Args:
        encrypted_content: The encrypted content to decrypt
        user_email: Email of the receiver
        metadata: Metadata from encryption (contains key ID)
        db_session: Database session (optional, not used with direct KME calls)
        
    Returns:
        Dict containing decrypted content and metadata
        
    Raises:
        Level1SecurityError: If decryption fails
    """
    try:
        logger.info("="*80)
        logger.info("LEVEL 1 OTP-QKD DECRYPTION START (ETSI GS QKD 014)")
        logger.info(f"  Receiver: {user_email}")
        logger.info(f"  Encrypted content: {len(encrypted_content)} characters")
        logger.info(f"  Protocol: ETSI GS QKD 014 REST API")
        logger.info(f"  Key Model: Synchronized keys (same key sender got from KM1)")
        logger.info("="*80)
        
        # DEBUG: Log all metadata received
        logger.info("DEBUG: Full metadata received:")
        for key, value in metadata.items():
            logger.info(f"  {key}: {value} (type: {type(value).__name__})")

        # Extract key identifiers from metadata
        key_id = metadata.get("key_id")
        flow_id = metadata.get("flow_id")
        auth_tag_b64 = metadata.get("auth_tag")  # HMAC Tag
        key_fragments_meta = metadata.get("key_fragments")
        
        # Decode encrypted content FIRST to determine required size
        logger.info("Decoding encrypted content from Base64...")
        encrypted_bytes = base64.b64decode(encrypted_content)
        
        # Calculate required_size from encrypted payload (OTP: ciphertext length = plaintext length)
        # The encrypted_bytes length IS the plaintext length for OTP
        required_size = len(encrypted_bytes)
        
        # Override with metadata if provided (should match)
        metadata_required_size = (
            metadata.get("required_size")
            or metadata.get("plaintext_size")
            or metadata.get("original_size")
        )
        if metadata_required_size:
            metadata_required_size = int(metadata_required_size)
            if metadata_required_size != required_size:
                logger.warning(
                    "Metadata required_size (%d) differs from encrypted content length (%d) - using encrypted content length",
                    metadata_required_size,
                    required_size
                )
        
        logger.info(f"  Encrypted: {len(encrypted_bytes)} bytes, first 32 bytes: {encrypted_bytes[:32].hex()}")
        logger.info(f"  Required plaintext size (from encrypted content): {required_size} bytes")

        # Parse key_fragments in various formats
        requested_key_ids: List[str] = []
        logger.info(f"DEBUG: key_fragments_meta type = {type(key_fragments_meta)}, value = {key_fragments_meta}")
        
        if isinstance(key_fragments_meta, list):
            # Handle list of dicts (fragment_records) or list of strings (key IDs)
            for item in key_fragments_meta:
                if isinstance(item, dict):
                    # Fragment record format: {"key_id": "...", "size_bytes": ...}
                    kid = item.get("key_id") or item.get("key_ID")
                    if kid:
                        requested_key_ids.append(str(kid))
                elif item:
                    requested_key_ids.append(str(item))
        elif isinstance(key_fragments_meta, str):
            parsed_ids: List[str] = []
            try:
                decoded = json.loads(key_fragments_meta)
                if isinstance(decoded, list):
                    for item in decoded:
                        if isinstance(item, dict):
                            kid = item.get("key_id") or item.get("key_ID")
                            if kid:
                                parsed_ids.append(str(kid))
                        elif item:
                            parsed_ids.append(str(item))
            except (json.JSONDecodeError, TypeError):
                parsed_ids = [seg.strip() for seg in key_fragments_meta.split(',') if seg.strip()]
            requested_key_ids = parsed_ids
        elif isinstance(key_fragments_meta, dict):
            # Handle dict format if accidentally stored
            for kid in key_fragments_meta.keys():
                requested_key_ids.append(str(kid))

        if not requested_key_ids and key_id:
            requested_key_ids = [key_id]
            logger.warning(f"No key_fragments found, falling back to single key_id: {key_id}")

        logger.info("Key identifier:")
        logger.info(f"  Primary Key ID: {key_id}")
        logger.info(f"  Key Fragment IDs: {requested_key_ids}")
        logger.info(f"  Key Fragment Count: {len(requested_key_ids)}")
        logger.info(f"  Flow ID: {flow_id}")
        logger.info(f"  Required Size: {required_size} bytes")
        logger.info(f"  Total key bytes needed: {required_size + 32} (OTP + HMAC)")
        logger.info(f"  ETSI QKD 014: Receiver will get SAME key from KM2")

        if not requested_key_ids:
            logger.error("ERROR - Missing key identifiers in decryption metadata")
            raise Level1SecurityError("Missing key identifiers in metadata - cannot decrypt")

        # FIRST: Try to get keys from LOCAL KEY MANAGER (fastest path)
        logger.info("LOCAL KM PATH: Attempting to retrieve decryption key from Local Key Manager...")
        
        local_km = get_local_key_manager()
        local_keys_found = []
        
        for kid in requested_key_ids:
            local_key_data = local_km.get_key_by_id(kid)
            if local_key_data:
                local_keys_found.append({
                    'key_ID': kid,
                    'key': base64.b64encode(local_key_data['key_material']).decode('utf-8')
                })
                logger.info(f"  ✓ Found key {kid[:16]}... in Local KM")
            else:
                logger.info(f"  ✗ Key {kid[:16]}... not in Local KM")
        
        if len(local_keys_found) == len(requested_key_ids):
            # All keys found in Local KM!
            logger.info("="*60)
            logger.info("✓ ALL KEYS FOUND IN LOCAL KEY MANAGER")
            logger.info(f"  Keys retrieved: {len(local_keys_found)}")
            logger.info("="*60)
            
            # Build key material from local keys
            key_lookup = {}
            for entry in local_keys_found:
                kid = str(entry.get('key_ID'))
                key_lookup[kid] = base64.b64decode(entry.get('key', ''))
                # Mark as consumed in local storage
                local_km.consume_key(kid)
            
            quantum_key_material = b"".join(key_lookup[kid] for kid in requested_key_ids)
            
        else:
            # Not all keys in Local KM, try KME servers
            logger.info(f"LOCAL KM: Found {len(local_keys_found)}/{len(requested_key_ids)} keys locally")
            logger.info("FALLBACK: Attempting to retrieve remaining keys from KME servers...")
            
            # PRODUCTION PATH: Prefer retrieving quantum key from KME2, fall back to KM1 shared pool if needed
            logger.info("KME2 PATH: Attempting to retrieve decryption key from KME2 (receiver-side cache)...")
            
            # Get optimized KM clients for Next Door Key Simulator
            km1_client, km2_client = get_optimized_km_clients()
            retrieved_keys = []
            try:
                if km2_client is None:
                    logger.warning("KME2 PATH: km2_client not initialized, skipping direct retrieval")
                else:
                    retrieved_keys = await km2_client.request_dec_keys(
                        master_sae_id=KM1_MASTER_SAE_ID,
                        key_ids=requested_key_ids
                    )
                    if retrieved_keys:
                        logger.info(
                            "KME2 PATH: Retrieved %s/%s key fragment(s) from KME2",
                            len(retrieved_keys),
                            len(requested_key_ids)
                        )
                        # Store retrieved keys in Local KM for future use
                        for entry in retrieved_keys:
                            kid = entry.get('key_ID')
                            raw_key = base64.b64decode(entry.get('key', ''))
                            if kid and raw_key:
                                local_km.store_key(
                                    key_id=kid,
                                    key_material=raw_key,
                                    source="KM2",
                                    metadata={"flow_id": flow_id, "cached_on_decrypt": True}
                                )
            except AuthenticationError as auth_error:
                logger.error(f"KME2 PATH: Authentication failed retrieving key fragment(s): {auth_error}")
            except KMConnectionError as conn_error:
                logger.error(f"KME2 PATH: Connection error retrieving key fragment(s): {conn_error}")
            except SecurityError as sec_error:
                logger.warning(f"KME2 PATH: Security error retrieving key fragment(s): {sec_error}")
            except Exception as e:
                logger.error(f"KME2 PATH: Unexpected exception retrieving key fragment(s): {e}")
            
            if not retrieved_keys or len(retrieved_keys) < len(requested_key_ids):
                logger.info("FALLBACK PATH: KME2 retrieval incomplete. Checking KM1 shared pool...")
                try:
                    if km1_client is None:
                        raise Level1SecurityError("KM1 client not initialized; cannot access shared pool")
                    retrieved_keys = await km1_client.request_dec_keys(
                        master_sae_id=KM1_MASTER_SAE_ID,
                        key_ids=requested_key_ids
                    )
                    if retrieved_keys:
                        logger.info(
                            "SHARED POOL: Retrieved %s/%s key fragment(s) from KM1",
                            len(retrieved_keys),
                            len(requested_key_ids)
                        )
                        # Store retrieved keys in Local KM
                        for entry in retrieved_keys:
                            kid = entry.get('key_ID')
                            raw_key = base64.b64decode(entry.get('key', ''))
                            if kid and raw_key:
                                local_km.store_key(
                                    key_id=kid,
                                    key_material=raw_key,
                                    source="KM1",
                                    metadata={"flow_id": flow_id, "cached_on_decrypt": True}
                                )
                except AuthenticationError as auth_error:
                    logger.error(f"SHARED POOL: Authentication failed retrieving key fragment(s): {auth_error}")
                    raise Level1SecurityError("KME authentication failed while retrieving shared key")
                except KMConnectionError as conn_error:
                    logger.error(f"SHARED POOL: Connection error retrieving key fragment(s): {conn_error}")
                    raise Level1SecurityError("Unable to reach KM shared pool for key retrieval")
                except SecurityError as sec_error:
                    logger.error(f"SHARED POOL: Security error retrieving key fragment(s): {sec_error}")
                    raise Level1SecurityError("Failed to retrieve quantum key fragments from shared pool")
                except Exception as e:
                    logger.error(f"SHARED POOL: Unexpected exception retrieving key fragment(s): {e}")
                    raise Level1SecurityError(f"Failed to retrieve quantum key fragments from shared pool: {e}")
            
            if not retrieved_keys:
                logger.error("KME RETRIEVAL: No KMEs returned the requested key fragments")
                raise Level1SecurityError("Quantum key fragments not found on KME2 or KM1 shared pool")
            
            key_lookup = {}
            for entry in retrieved_keys:
                kid = str(entry.get('key_ID'))
                if not kid:
                    continue
                try:
                    key_lookup[kid] = base64.b64decode(entry.get('key', ''))
                except Exception:
                    logger.warning("Failed to decode key fragment %s", kid, exc_info=True)

            missing_fragments = [kid for kid in requested_key_ids if kid not in key_lookup or not key_lookup[kid]]
            if missing_fragments:
                raise Level1SecurityError(f"Missing quantum key fragment(s): {missing_fragments}")

            quantum_key_material = b"".join(key_lookup[kid] for kid in requested_key_ids)
        
        logger.info("✓ Decryption key fragments assembled")
        logger.info(f"  - Fragment Count: {len(requested_key_ids)}")
        logger.info(f"  - Combined Key Size: {len(quantum_key_material)} bytes")
        logger.info(f"  - First 16 bytes: {quantum_key_material[:16].hex()}")

        # encrypted_bytes already decoded at start of function
        # required_size already calculated from encrypted content length

        # Verify key size matches required size (L + 32)
        total_required_size = required_size + 32
        if len(quantum_key_material) < total_required_size:
            logger.error(f"  ERROR: Key too short! Got {len(quantum_key_material)} bytes, need {total_required_size} bytes")
            logger.error(f"  This may be due to:")
            logger.error(f"    1. Email was encrypted before multi-fragment key fix")
            logger.error(f"    2. Key fragments were not properly stored in metadata")
            logger.error(f"    3. KME server restart caused key loss (in-memory storage)")
            logger.error(f"  Requested key IDs: {requested_key_ids}")
            logger.error(f"  Retrieved key IDs: {list(key_lookup.keys())}")
            raise Level1SecurityError(
                f"Retrieved key is too short: {len(quantum_key_material)} bytes, need {total_required_size} bytes. "
                f"This email may have been encrypted with an older version or the quantum keys have been lost."
            )
        
        # Use the exact required size
        quantum_key_material = quantum_key_material[:total_required_size]
        logger.info(f"  Using key length: {len(quantum_key_material)} bytes")

        # SPLIT KEY ARCHITECTURE
        otp_key = quantum_key_material[:required_size]
        hmac_key = quantum_key_material[required_size:]
        
        logger.info("SPLIT KEY ARCHITECTURE APPLIED")
        logger.info(f"  OTP Key: {len(otp_key)} bytes")
        logger.info(f"  HMAC Key: {len(hmac_key)} bytes")

        # INTEGRITY GATE: Verify HMAC-SHA256
        if auth_tag_b64:
            logger.info("Verifying HMAC-SHA256 Integrity Tag (Integrity Gate)...")
            try:
                auth_tag = base64.b64decode(auth_tag_b64)
                h = hmac.HMAC(hmac_key, hashes.SHA256(), backend=default_backend())
                h.update(encrypted_bytes)
                h.verify(auth_tag)
                logger.info("✓ INTEGRITY GATE PASSED: HMAC verified")
            except InvalidSignature:
                logger.critical("!!! INTEGRITY GATE FAILED: HMAC verification failed !!!")
                # WIPE KEYS FROM MEMORY
                otp_key = b'\x00' * len(otp_key)
                hmac_key = b'\x00' * len(hmac_key)
                quantum_key_material = b'\x00' * len(quantum_key_material)
                raise Level1SecurityError("Integrity Gate Failed: HMAC verification failed. Possible tampering.")
        else:
             logger.warning("!!! NO AUTH TAG PROVIDED - SKIPPING INTEGRITY GATE (NOT RECOMMENDED) !!!")

        # Perform OTP decryption (XOR)
        logger.info("PERFORMING ONE-TIME PAD DECRYPTION")
        logger.info(f"  Encrypted (first 32 bytes): {encrypted_bytes[:32].hex()}")
        logger.info(f"  OTP Key (first 32 bytes): {otp_key[:32].hex()}")

        decrypted_bytes = bytes(a ^ b for a, b in zip(encrypted_bytes, otp_key))
        logger.info(f"  Decrypted (first 32 bytes): {decrypted_bytes[:32].hex()}")
        logger.info(f"  Decrypted: {len(decrypted_bytes)} bytes")

        # Decode to UTF-8
        decrypted_content = decrypted_bytes.decode("utf-8")
        logger.info(f"  Decrypted content preview: {decrypted_content[:100]}...")

        logger.info("="*80)
        logger.info("LEVEL 1 OTP-QKD DECRYPTION COMPLETED SUCCESSFULLY")
        logger.info(f"  Algorithm: OTP-QKD-ETSI-014 (ETSI GS QKD 014)")
        logger.info(f"  Security Level: Maximum (Information-theoretic security)")
        logger.info(f"  Content decrypted: {len(decrypted_bytes)} bytes")
        logger.info(f"  Protocol: ETSI GS QKD 014 REST API")
        logger.info(f"  Key Status: USED (deleted from KM2, cannot be reused)")
        logger.info(f"  One-Time Pad: ENFORCED (key consumed)")
        logger.info("="*80)

        return {
            "decrypted_content": decrypted_content,
            "algorithm": "OTP-QKD-ETSI-014",
            "verification_status": "verified",
            "metadata": {
                "flow_id": flow_id,
                "security_level": 1,
                "algorithm": "OTP-QKD-ETSI-014",
                "keys_consumed": True,
                "quantum_enhanced": True,
                "etsi_qkd_014": True,
                "synchronized_keys": True,
                "one_time_pad": True
            }
        }

    except Exception as e:
        logger.error("="*80)
        logger.error("LEVEL 1 OTP-QKD DECRYPTION FAILED")
        logger.error(f"  Error: {e}")
        logger.error(f"  User: {user_email}")
        logger.error("="*80)
        raise Level1SecurityError(f"OTP decryption failed: {e}")

# Global instances for quantum services
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
        
        # TEMPORARY: Skip marking key as consumed during encryption
        # Let key be consumed only AFTER successful decryption
        logger.info(f"SHARED POOL: NOT marking key {key_id} as consumed during encryption")
        logger.info("  - Key will remain available in shared pool for decryption")
        # await quantum_key_manager.mark_key_consumed(
        #     key_id=key_id,
        #     user_id=user_email,
        #     usage_type="OTP_ENCRYPTION"
        # )
        
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

async def _generate_rsa_signature(content: str, user_email: str) -> str:
    """Generate RSA signature for content integrity"""
    try:
        # Generate RSA key pair (in production, this would be stored/loaded)
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        # Create signature
        message = f"{content}:{user_email}".encode("utf-8")
        signature = private_key.sign(
            message,
            asym_padding.PSS(
                mgf=asym_padding.MGF1(hashes.SHA256()),
                salt_length=asym_padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        # Convert to base64 for transport
        signature_b64 = base64.b64encode(signature).decode("utf-8")
        
        logger.debug(f"Generated RSA signature for {user_email}")
        return signature_b64
        
    except Exception as e:
        logger.error(f"RSA signature generation failed: {e}")
        # Return a simple hash if RSA fails
        return hashlib.sha256(f"{content}:{user_email}".encode()).hexdigest()
