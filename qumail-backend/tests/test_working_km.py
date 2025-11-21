#!/usr/bin/env python3
"""
Test script for working with real KM servers using a hybrid approach.
This script focuses only on the working endpoints and uses fallback mechanisms.

Usage:
    python -m tests.test_working_km
"""

import os
import sys
import asyncio
import logging
import json
import base64
import binascii
import uuid
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

# Add the app directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the required modules
from app.services.optimized_km_client import OptimizedKMClient
from app.services.real_qkd_client import RealQKDClient
from app.config import get_settings
from app.security.encryption import (
    encrypt_level1_otp, 
    decrypt_level1_otp,
    encrypt_level2_aes_gcm, 
    decrypt_level2_aes_gcm,
    encrypt_level3_pqc, 
    decrypt_level3_pqc,
    encrypt_level4_rsa_aes, 
    decrypt_level4_rsa_aes
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# KME server locations
KME1_URL = "https://localhost:13000"
KME2_URL = "https://localhost:14000"

# SAE IDs
SENDER_SAE_ID = 1    # SAE ID of sender (Alice)
RECEIVER_SAE_ID = 3  # SAE ID of receiver (Bob)

# Certificate paths for KME 1
KME1_CERT_DIR = os.path.abspath(os.path.join(
    os.path.dirname(__file__), 
    '..', '..', 'qkd_kme_server-master', 'certs', 'kme-1-local-zone'
))

# Certificate paths for KME 2
KME2_CERT_DIR = os.path.abspath(os.path.join(
    os.path.dirname(__file__), 
    '..', '..', 'qkd_kme_server-master', 'certs', 'kme-2-local-zone'
))

# Raw key paths
RAW_KEYS_DIR = os.path.abspath(os.path.join(
    os.path.dirname(__file__),
    '..', '..', 'qkd_kme_server-master', 'raw_keys'
))

# Test data
TEST_MESSAGE = "This is a secret message that needs quantum encryption!"


class HybridKMClient:
    """
    Hybrid KM client that uses both OptimizedKMClient for status 
    and RealQKDClient for raw key fallback
    """
    def __init__(self, kme_url: str, sae_id: int, certs_dir: str, raw_keys_dir: str, zone_name: str):
        """
        Initialize hybrid client
        
        Args:
            kme_url: Base URL of the KM server
            sae_id: SAE ID
            certs_dir: Directory containing certificates
            raw_keys_dir: Directory containing raw keys
            zone_name: Zone name (kme-1-local-zone or kme-2-local-zone)
        """
        # Set up optimized KM client for status and other GET operations
        client_cert_path = os.path.join(certs_dir, f"client_{sae_id}_cert.pem")
        client_key_path = os.path.join(certs_dir, f"client_{sae_id}.key")
        ca_cert_path = os.path.join(certs_dir, "ca.crt")
        
        self.opt_client = OptimizedKMClient(
            base_url=kme_url,
            sae_id=sae_id,
            client_cert_path=client_cert_path,
            client_key_path=client_key_path,
            ca_cert_path=ca_cert_path
        )
        
        # Set up real QKD client for raw key fallback
        self.real_client = RealQKDClient(
            zone_name=zone_name,
            sae_id=sae_id,
            base_path=os.path.join(os.path.dirname(__file__), '..', '..', 'qkd_kme_server-master')
        )
        
        self.sae_id = sae_id
    
    async def check_key_status(self, slave_sae_id: int) -> Dict[str, Any]:
        """Check key status for slave SAE"""
        return await self.opt_client.check_key_status(slave_sae_id)
    
    async def get_server_status(self) -> Dict[str, Any]:
        """Get server status"""
        return await self.opt_client.get_status()
    
    async def request_enc_keys(self, slave_sae_id: int, number: int = 1) -> List[Dict[str, Any]]:
        """
        Request encryption keys with fallback to raw keys
        
        This method tries to get keys from OptimizedKMClient first,
        and if that fails, falls back to RealQKDClient raw keys
        """
        try:
            # First attempt to get keys from KME server
            logger.info(f"Attempting to get keys from KME server for SAE {slave_sae_id}")
            keys = await self.opt_client.request_enc_keys(slave_sae_id, number)
            return keys
        except Exception as e:
            logger.warning(f"Failed to get keys from KME server: {e}, falling back to raw keys")
            
            # Fall back to raw keys
            raw_keys = self.real_client.get_raw_keys(slave_sae_id, number)
            
            # Convert raw keys to the format expected by encryption functions
            formatted_keys = []
            for i, key_data in enumerate(raw_keys):
                key_id = str(uuid.uuid4())
                key_b64 = base64.b64encode(key_data).decode('utf-8')
                
                formatted_keys.append({
                    "key_ID": key_id,
                    "key": key_b64,
                    "key_size": len(key_data) * 8
                })
            
            logger.info(f"Successfully retrieved {len(formatted_keys)} raw keys as fallback")
            return formatted_keys


async def main():
    """Main test function"""
    try:
        # Initialize hybrid clients
        logger.info("Initializing Hybrid KM clients...")
        kme1_client = HybridKMClient(
            kme_url=KME1_URL,
            sae_id=SENDER_SAE_ID,
            certs_dir=KME1_CERT_DIR,
            raw_keys_dir=RAW_KEYS_DIR,
            zone_name="kme-1-local-zone"
        )
        
        kme2_client = HybridKMClient(
            kme_url=KME2_URL,
            sae_id=RECEIVER_SAE_ID,
            certs_dir=KME2_CERT_DIR,
            raw_keys_dir=RAW_KEYS_DIR,
            zone_name="kme-2-local-zone"
        )
        
        logger.info("Hybrid KM clients initialized successfully")
        
        # Test 1: Check server status for both KMEs
        logger.info("===== Test 1: Checking KME server status =====")
        kme1_status = await kme1_client.get_server_status()
        kme2_status = await kme2_client.get_server_status()
        
        logger.info(f"KME1 Status: {json.dumps(kme1_status)}")
        logger.info(f"KME2 Status: {json.dumps(kme2_status)}")
        
        # Test 2: Check key status
        logger.info("===== Test 2: Checking key status =====")
        kme1_key_status = await kme1_client.check_key_status(RECEIVER_SAE_ID)
        kme2_key_status = await kme2_client.check_key_status(SENDER_SAE_ID)
        
        logger.info(f"KME1->KME2 Key Status: {json.dumps(kme1_key_status)}")
        logger.info(f"KME2->KME1 Key Status: {json.dumps(kme2_key_status)}")
        
        # Test 3: Request encryption keys with fallback
        logger.info("===== Test 3: Requesting encryption keys with fallback =====")
        keys_alice_to_bob = await kme1_client.request_enc_keys(RECEIVER_SAE_ID, 1)
        logger.info(f"Retrieved {len(keys_alice_to_bob)} keys for Alice->Bob encryption")
        
        keys_bob_to_alice = await kme2_client.request_enc_keys(SENDER_SAE_ID, 1)
        logger.info(f"Retrieved {len(keys_bob_to_alice)} keys for Bob->Alice encryption")
        
        # Test 4: Level 1 encryption (OTP)
        logger.info("===== Test 4: Testing Level 1 (OTP) encryption =====")
        # Get quantum keys
        otp_key = base64.b64decode(keys_alice_to_bob[0]["key"])
        otp_key_id = keys_alice_to_bob[0]["key_ID"]
        
        # Encrypt with Level 1 (OTP)
        encrypted_data, _ = encrypt_level1_otp(TEST_MESSAGE.encode(), otp_key)
        logger.info(f"Level 1 (OTP) encrypted: {binascii.hexlify(encrypted_data).decode()}")
        
        # Decrypt with Level 1 (OTP)
        decrypted_data = decrypt_level1_otp(encrypted_data, otp_key)
        decrypted_message = decrypted_data.decode()
        logger.info(f"Level 1 (OTP) decrypted: {decrypted_message}")
        
        assert decrypted_message == TEST_MESSAGE, "Level 1 (OTP) decryption failed!"
        logger.info("Level 1 (OTP) encryption test passed!")
        
        # Test 5: Level 2 encryption (AES-GCM)
        logger.info("===== Test 5: Testing Level 2 (AES-GCM) encryption =====")
        # Get quantum keys
        aes_key = base64.b64decode(keys_alice_to_bob[0]["key"])[:32]  # 256-bit key
        aes_key_id = keys_alice_to_bob[0]["key_ID"]
        
        # Encrypt with Level 2 (AES-GCM)
        encrypted_data, nonce = encrypt_level2_aes_gcm(TEST_MESSAGE.encode(), aes_key)
        logger.info(f"Level 2 (AES-GCM) encrypted: {binascii.hexlify(encrypted_data).decode()}")
        
        # Decrypt with Level 2 (AES-GCM)
        decrypted_data = decrypt_level2_aes_gcm(encrypted_data, aes_key, nonce)
        decrypted_message = decrypted_data.decode()
        logger.info(f"Level 2 (AES-GCM) decrypted: {decrypted_message}")
        
        assert decrypted_message == TEST_MESSAGE, "Level 2 (AES-GCM) decryption failed!"
        logger.info("Level 2 (AES-GCM) encryption test passed!")
        
        # Test 6: Level 3 encryption (PQC)
        logger.info("===== Test 6: Testing Level 3 (PQC) encryption =====")
        # Encrypt with Level 3 (PQC)
        encrypted_data, encap_key = encrypt_level3_pqc(TEST_MESSAGE.encode())
        logger.info(f"Level 3 (PQC) encrypted: {len(encrypted_data)} bytes")
        
        # Decrypt with Level 3 (PQC)
        decrypted_data = decrypt_level3_pqc(encrypted_data, encap_key)
        decrypted_message = decrypted_data.decode()
        logger.info(f"Level 3 (PQC) decrypted: {decrypted_message}")
        
        assert decrypted_message == TEST_MESSAGE, "Level 3 (PQC) decryption failed!"
        logger.info("Level 3 (PQC) encryption test passed!")
        
        # Test 7: Level 4 encryption (RSA+AES)
        logger.info("===== Test 7: Testing Level 4 (RSA+AES) encryption =====")
        # Encrypt with Level 4 (RSA+AES)
        encrypted_data, encrypted_key = encrypt_level4_rsa_aes(TEST_MESSAGE.encode())
        logger.info(f"Level 4 (RSA+AES) encrypted: {len(encrypted_data)} bytes")
        
        # Decrypt with Level 4 (RSA+AES)
        decrypted_data = decrypt_level4_rsa_aes(encrypted_data, encrypted_key)
        decrypted_message = decrypted_data.decode()
        logger.info(f"Level 4 (RSA+AES) decrypted: {decrypted_message}")
        
        assert decrypted_message == TEST_MESSAGE, "Level 4 (RSA+AES) decryption failed!"
        logger.info("Level 4 (RSA+AES) encryption test passed!")
        
        logger.info("===== All tests passed! =====")
        
    finally:
        # Clean up resources
        if 'kme1_client' in locals():
            await kme1_client.opt_client.close()
        if 'kme2_client' in locals():
            await kme2_client.opt_client.close()


if __name__ == "__main__":
    asyncio.run(main())