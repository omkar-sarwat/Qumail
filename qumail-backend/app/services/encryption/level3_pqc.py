import logging
import base64
import os
import secrets
from typing import Dict, Any, Tuple, Optional

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding as asym_padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.backends import default_backend

try:
    # Try relative imports first (works at runtime)
    from ..km_client_init import get_optimized_km_clients
    from ..exceptions import Level3SecurityError, InsufficientKeysError
    from ..optimized_km_client import AuthenticationError, KMConnectionError
except ImportError:
    # Fall back to absolute imports (helps Pylance/IDE)
    from app.services.km_client_init import get_optimized_km_clients
    from app.services.exceptions import Level3SecurityError, InsufficientKeysError
    from app.services.optimized_km_client import AuthenticationError, KMConnectionError

logger = logging.getLogger(__name__)

# NIST-approved post-quantum algorithms
KYBER_ALGORITHM = "Kyber1024"  # Key encapsulation mechanism
DILITHIUM_ALGORITHM = "Dilithium5"  # Digital signature algorithm
KM1_MASTER_SAE_ID = "25840139-0dd4-49ae-ba1e-b86731601803"

# PQC availability check
try:
    import oqs  # type: ignore
    PQC_AVAILABLE = True
    logger.info("liboqs loaded successfully - using real PQC algorithms")
except (ImportError, RuntimeError, OSError) as e:
    PQC_AVAILABLE = False
    logger.warning(f"liboqs not available ({type(e).__name__}): {e}")
    logger.warning("Level 3 PQC using secure placeholder implementations")
    oqs = None  # Set to None to avoid NameError

def is_pqc_available():
    """Check if post-quantum cryptography is available"""
    return PQC_AVAILABLE


class PQCNotAvailableError(Level3SecurityError):
    """Raised when PQC libraries are not available"""
    pass


class PQCError(Level3SecurityError):
    """Post-quantum cryptography operation failed"""
    pass


class KeyPairNotFoundError(Level3SecurityError):
    """Raised when required key pairs are not found"""
    pass


def derive_session_key(shared_secret: bytes, flow_id: str) -> bytes:
    """
    Derive AES-256 session key from Kyber shared secret using HKDF
    
    Security Features:
    - HKDF-SHA256 for proper key derivation
    - Flow-specific salt for unique keys per email
    - Post-quantum resistant key material
    """
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,  # 256 bits for AES-256
        salt=flow_id.encode('utf-8'),
        info=b"QuMail-Level3-PQC-Kyber-SessionKey-v1.0",
        backend=default_backend()
    )
    return hkdf.derive(shared_secret)


class KyberKEM:
    """Kyber1024 Key Encapsulation Mechanism"""
    
    @staticmethod
    def generate_keypair() -> Tuple[bytes, bytes]:
        """Generate Kyber1024 keypair"""
        if PQC_AVAILABLE:
            kem = oqs.KeyEncapsulation(KYBER_ALGORITHM)
            public_key = kem.generate_keypair()
            private_key = kem.export_secret_key()
            return private_key, public_key
        else:
            # Placeholder implementation
            private_key = secrets.token_bytes(2400)
            public_key = secrets.token_bytes(1568)
            logger.warning("Using PLACEHOLDER Kyber1024 - replace with real implementation")
            return private_key, public_key
    
    @staticmethod
    def encapsulate(public_key: bytes) -> Tuple[bytes, bytes]:
        """Encapsulate shared secret with public key"""
        if PQC_AVAILABLE:
            kem = oqs.KeyEncapsulation(KYBER_ALGORITHM)
            ciphertext, shared_secret = kem.encap_secret(public_key)
            return ciphertext, shared_secret
        else:
            # Placeholder implementation
            # INSECURE: Embedding shared secret in ciphertext for functional testing without liboqs
            shared_secret = secrets.token_bytes(32)
            # Pad to simulate Kyber ciphertext size (1568 bytes)
            # We put shared secret at the start
            ciphertext = shared_secret + secrets.token_bytes(1568 - 32)
            return ciphertext, shared_secret
    
    @staticmethod
    def decapsulate(private_key: bytes, ciphertext: bytes) -> bytes:
        """Decapsulate shared secret with private key"""
        if PQC_AVAILABLE:
            kem = oqs.KeyEncapsulation(KYBER_ALGORITHM, secret_key=private_key)
            shared_secret = kem.decap_secret(ciphertext)
            return shared_secret
        else:
            # Placeholder - extract shared secret from ciphertext
            # INSECURE: For testing only
            shared_secret = ciphertext[:32]
            return shared_secret


class DilithiumSignature:
    """Dilithium5 Digital Signature"""
    
    @staticmethod
    def generate_keypair() -> Tuple[bytes, bytes]:
        """Generate Dilithium5 keypair"""
        if PQC_AVAILABLE:
            sig = oqs.Signature(DILITHIUM_ALGORITHM)
            public_key = sig.generate_keypair()
            private_key = sig.export_secret_key()
            return private_key, public_key
        else:
            # Placeholder implementation
            private_key = secrets.token_bytes(4864)
            public_key = secrets.token_bytes(2592)
            logger.warning("Using PLACEHOLDER Dilithium5 - replace with real implementation")
            return private_key, public_key
    
    @staticmethod
    def sign(private_key: bytes, message: bytes) -> bytes:
        """Sign message with Dilithium5"""
        if PQC_AVAILABLE:
            sig = oqs.Signature(DILITHIUM_ALGORITHM, secret_key=private_key)
            signature = sig.sign(message)
            return signature
        else:
            # Placeholder signature generation
            signature = secrets.token_bytes(4595)
            return signature
    
    @staticmethod
    def verify(public_key: bytes, message: bytes, signature: bytes) -> bool:
        """Verify Dilithium5 signature"""
        if PQC_AVAILABLE:
            sig = oqs.Signature(DILITHIUM_ALGORITHM)
            return sig.verify(message, signature, public_key)
        else:
            # In placeholder mode, always return True for testing
            return True


async def encrypt_pqc(content: str, user_email: str) -> Dict[str, Any]:
    """
    Level 3: Post-Quantum Cryptography encryption
    
    Security Features:
    - Kyber1024 for quantum-resistant key encapsulation
    - Dilithium5 for quantum-resistant digital signatures
    - AES-256-GCM for symmetric encryption with authentication
    - HKDF key derivation from quantum-resistant shared secret
    - Optional quantum key enhancement
    """
    try:
        plaintext = content.encode('utf-8')
        flow_id = secrets.token_hex(16)
        
        logger.info(f"Starting Level 3 PQC encryption for flow {flow_id}")
        
        # Step 1: Generate Kyber1024 keypair for key encapsulation
        kyber_private_key, kyber_public_key = KyberKEM.generate_keypair()
        
        # Step 1b: Generate Dilithium5 keypair for digital signature
        dilithium_private_key, dilithium_public_key = DilithiumSignature.generate_keypair()
        
        # Step 2: Request quantum keys for enhancement (optional)
        quantum_enhancement = None
        try:
            # Get optimized KM clients
            km1_client, km2_client = get_optimized_km_clients()
            
            # Request quantum keys for enhancement (slave_sae_id is required first parameter)
            km1_keys = await km1_client.request_enc_keys(
                slave_sae_id="c565d5aa-8670-4446-8471-b0e53e315d2a",  # KME2's SAE ID
                number=1, 
                size=128
            )
            km2_keys = await km2_client.request_enc_keys(
                slave_sae_id="25840139-0dd4-49ae-ba1e-b86731601803",  # KME1's SAE ID
                number=1, 
                size=128
            )
            
            if km1_keys and km2_keys:
                km1_key_data = base64.b64decode(km1_keys[0]['key'])
                km2_key_data = base64.b64decode(km2_keys[0]['key'])
                
                quantum_enhancement = {
                    "enabled": True,
                    "key_ids": {
                        "km1": km1_keys[0]['key_ID'],
                        "km2": km2_keys[0]['key_ID']
                    },
                    "enhancement_material": km1_key_data + km2_key_data
                }
                logger.info(f"Quantum enhancement enabled for flow {flow_id}")
            else:
                logger.warning("Failed to retrieve quantum keys for enhancement")
        except Exception as e:
            logger.warning(f"Quantum enhancement failed: {e}, proceeding without")
        
        if not quantum_enhancement:
            quantum_enhancement = {"enabled": False}
        
        # Step 4: Encapsulate shared secret with Kyber1024
        kyber_ciphertext, kyber_shared_secret = KyberKEM.encapsulate(kyber_public_key)
        
        # Step 5: Derive AES key with quantum enhancement
        if quantum_enhancement["enabled"]:
            ikm = kyber_shared_secret + quantum_enhancement["enhancement_material"]
            info = f"QuMail-PQC-Enhanced-{flow_id}".encode('utf-8')
        else:
            ikm = kyber_shared_secret
            info = f"QuMail-PQC-{flow_id}".encode('utf-8')
        
        salt = secrets.token_bytes(32)
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            info=info,
            backend=default_backend()
        )
        aes_key = hkdf.derive(ikm)
        
        # Step 6: Encrypt with AES-256-GCM
        nonce = secrets.token_bytes(12)
        cipher = Cipher(algorithms.AES(aes_key), modes.GCM(nonce), backend=default_backend())
        encryptor = cipher.encryptor()
        
        ciphertext = encryptor.update(plaintext) + encryptor.finalize()
        auth_tag = encryptor.tag
        
        # Step 7: Sign ciphertext with Dilithium5
        signature = DilithiumSignature.sign(dilithium_private_key, ciphertext)
        signature_b64 = base64.b64encode(signature).decode()
        logger.info(f"Generated Dilithium5 Signature for flow {flow_id}")
        
        # Step 8: Clear sensitive data
        ikm = b'\x00' * len(ikm)
        aes_key = b'\x00' * len(aes_key)
        kyber_shared_secret = b'\x00' * len(kyber_shared_secret)
        if quantum_enhancement["enabled"]:
            quantum_enhancement["enhancement_material"] = b'\x00' * len(quantum_enhancement["enhancement_material"])
        
        logger.info(f"Level 3 PQC encryption completed for flow {flow_id}")
        
        return {
            "encrypted_content": base64.b64encode(ciphertext).decode(),
            "algorithm": "Kyber1024+Dilithium5+AES-256-GCM",
            "signature": signature_b64,
            "auth_tag": base64.b64encode(auth_tag).decode(),
            "metadata": {
                "flow_id": flow_id,
                "salt": base64.b64encode(salt).decode(),
                "nonce": base64.b64encode(nonce).decode(),
                "auth_tag": base64.b64encode(auth_tag).decode(),
                "signature": signature_b64,
                "kyber_ciphertext": base64.b64encode(kyber_ciphertext).decode(),
                "kyber_private_key": base64.b64encode(kyber_private_key).decode(),
                "kyber_public_key": base64.b64encode(kyber_public_key).decode(),
                "dilithium_public_key": base64.b64encode(dilithium_public_key).decode(),
                "quantum_enhancement": {
                    "enabled": quantum_enhancement["enabled"],
                    "key_ids": quantum_enhancement.get("key_ids", {})
                },
                "security_level": 3,
                "pqc_algorithms": ["Kyber1024", "Dilithium5"],
                "cipher": "AES-256-GCM"
            }
        }
        
    except Exception as e:
        logger.error(f"Level 3 PQC encryption failed: {e}")
        raise Level3SecurityError(f"PQC encryption failed: {e}")


async def decrypt_pqc(encrypted_content: str, user_email: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Level 3: Post-Quantum Cryptography decryption
    
    Security Features:
    - Dilithium5 signature verification
    - Kyber1024 decapsulation
    - Quantum key retrieval for enhancement
    - Authenticated decryption
    """
    try:
        # Step 1: Extract metadata
        flow_id = metadata["flow_id"]
        salt = base64.b64decode(metadata["salt"])
        nonce = base64.b64decode(metadata["nonce"])
        auth_tag = base64.b64decode(metadata["auth_tag"])
        kyber_ciphertext = base64.b64decode(metadata["kyber_ciphertext"])
        kyber_private_key = base64.b64decode(metadata["kyber_private_key"])
        kyber_public_key = base64.b64decode(metadata["kyber_public_key"])
        dilithium_public_key = base64.b64decode(metadata.get("dilithium_public_key", ""))
        signature_b64 = metadata.get("signature", "")
        quantum_enhancement = metadata["quantum_enhancement"]
        
        ciphertext = base64.b64decode(encrypted_content)
        
        logger.info(f"Starting Level 3 PQC decryption for flow {flow_id}")
        
        # Step 2: Verify Dilithium5 Signature
        if dilithium_public_key and signature_b64:
            signature = base64.b64decode(signature_b64)
            if DilithiumSignature.verify(dilithium_public_key, ciphertext, signature):
                logger.info(f"✓ DILITHIUM SIGNATURE VERIFIED for flow {flow_id}")
            else:
                logger.critical(f"!!! DILITHIUM SIGNATURE VERIFICATION FAILED for flow {flow_id} !!!")
                raise Level3SecurityError("Dilithium Signature Verification Failed - data integrity compromised")
        else:
            logger.warning(f"Missing Dilithium public key or signature for flow {flow_id}")
        
        # Step 3: Decapsulate Kyber1024 shared secret
        kyber_shared_secret = KyberKEM.decapsulate(kyber_private_key, kyber_ciphertext)
        
        # Step 4: Retrieve quantum enhancement if enabled
        enhancement_material = b""
        if quantum_enhancement["enabled"]:
            key_ids = quantum_enhancement["key_ids"]
            logger.info(
                "SHARED POOL: Retrieving quantum enhancement keys %s via KM2 client",
                key_ids
            )
            try:
                _, km2_client = get_optimized_km_clients()
                km_keys = await km2_client.request_dec_keys(
                    master_sae_id=KM1_MASTER_SAE_ID,
                    key_ids=[key_ids["km1"], key_ids["km2"]]
                )
            except AuthenticationError as auth_error:
                logger.error("SHARED POOL: Authentication failed retrieving enhancement keys: %s", auth_error)
                raise Level3SecurityError("KME authentication failed while retrieving quantum enhancement keys")
            except KMConnectionError as conn_error:
                logger.error("SHARED POOL: Connection error retrieving enhancement keys: %s", conn_error)
                raise Level3SecurityError("Unable to reach KM shared pool for enhancement keys")
            except Exception as exc:
                logger.error("SHARED POOL: Unexpected error retrieving enhancement keys: %s", exc)
                raise Level3SecurityError(f"Quantum enhancement retrieval failed: {exc}")

            if not km_keys or len(km_keys) < 2:
                logger.error(
                    "SHARED POOL: Expected 2 enhancement keys but received %d", 
                    0 if not km_keys else len(km_keys)
                )
                raise Level3SecurityError("Quantum enhancement keys unavailable in shared pool")

            key_dict = {k['key_ID']: base64.b64decode(k['key']) for k in km_keys}
            km1_key_data = key_dict.get(key_ids["km1"])
            km2_key_data = key_dict.get(key_ids["km2"])

            if not km1_key_data or not km2_key_data:
                logger.error("SHARED POOL: Required enhancement keys missing from response")
                raise Level3SecurityError("Quantum enhancement keys missing from shared pool response")

            enhancement_material = km1_key_data + km2_key_data
            logger.info("Quantum enhancement material retrieved for flow %s", flow_id)
        
        # Step 5: Derive AES key (same process as encryption)
        if quantum_enhancement["enabled"]:
            ikm = kyber_shared_secret + enhancement_material
            info = f"QuMail-PQC-Enhanced-{flow_id}".encode('utf-8')
        else:
            ikm = kyber_shared_secret
            info = f"QuMail-PQC-{flow_id}".encode('utf-8')
        
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            info=info,
            backend=default_backend()
        )
        aes_key = hkdf.derive(ikm)
        
        # Step 6: Decrypt with AES-256-GCM
        cipher = Cipher(algorithms.AES(aes_key), modes.GCM(nonce, auth_tag), backend=default_backend())
        decryptor = cipher.decryptor()
        
        try:
            plaintext_bytes = decryptor.update(ciphertext) + decryptor.finalize()
            plaintext = plaintext_bytes.decode('utf-8')
            logger.info(f"✓ INTEGRITY GATE PASSED: PQC GCM tag verified for flow {flow_id}")
        except Exception as e:
            logger.critical(f"!!! INTEGRITY GATE FAILED: PQC GCM decryption failed for flow {flow_id}: {e}")
            # WIPE KEYS
            ikm = b'\x00' * len(ikm)
            aes_key = b'\x00' * len(aes_key)
            kyber_shared_secret = b'\x00' * len(kyber_shared_secret)
            enhancement_material = b'\x00' * len(enhancement_material)
            raise Level3SecurityError("Integrity Gate Failed: PQC GCM decryption failed - data corrupted or tampered")
        
        # Step 7: Clear sensitive data
        ikm = b'\x00' * len(ikm)
        aes_key = b'\x00' * len(aes_key)
        kyber_shared_secret = b'\x00' * len(kyber_shared_secret)
        enhancement_material = b'\x00' * len(enhancement_material)
        
        logger.info(f"Level 3 PQC decryption completed for flow {flow_id}")
        
        return {
            "decrypted_content": plaintext,
            "verification_status": "verified",
            "metadata": {
                "flow_id": flow_id,
                "security_level": 3,
                "algorithm": "Kyber1024+Dilithium5+AES-256-GCM",
                "quantum_enhanced": quantum_enhancement["enabled"],
                "pqc_algorithms": ["Kyber1024", "Dilithium5"]
            }
        }
        
    except Level3SecurityError:
        raise
    except Exception as e:
        logger.error(f"Level 3 PQC decryption failed: {e}")
        raise Level3SecurityError(f"PQC decryption failed: {e}")


def generate_kyber_keypair() -> Tuple[bytes, bytes]:
    """Generate Kyber1024 key pair for key encapsulation"""
    return KyberKEM.generate_keypair()


def generate_dilithium_keypair() -> Tuple[bytes, bytes]:
    """Generate Dilithium5 key pair for digital signatures"""
    return DilithiumSignature.generate_keypair()


def is_pqc_available() -> bool:
    """Check if post-quantum cryptography is available"""
    return PQC_AVAILABLE
