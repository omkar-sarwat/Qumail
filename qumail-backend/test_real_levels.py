#!/usr/bin/env python
"""
Test script for testing all encryption levels with real Quantum Key Management servers.
This script tests all four encryption levels using real KM servers for quantum key distribution.
"""

import os
import sys
import logging
import base64
import asyncio
import ssl
import httpx
from typing import Dict, Any, List, Union
import uuid
import secrets
import traceback

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ensure we can import from the app package
sys.path.append(os.path.dirname(__file__))

# Import the required modules
from app.config import get_settings

async def setup_ssl_context(client_cert_path, client_key_path, ca_cert_path):
    """Create SSL context with client certificate authentication"""
    ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ssl_context.verify_mode = ssl.CERT_REQUIRED
    ssl_context.check_hostname = False  # KM uses localhost
    
    # Load CA certificate for server verification
    ssl_context.load_verify_locations(cafile=ca_cert_path)
    
    # Load client certificate and key
    ssl_context.load_cert_chain(certfile=client_cert_path, keyfile=client_key_path)
    
    return ssl_context

async def request_quantum_key(client, receiver_sae_id):
    """Request quantum key from KM server"""
    # Check key status first
    response = await client.get(f"/api/v1/keys/{receiver_sae_id}/status")
    response.raise_for_status()
    
    status = response.json()
    logger.info(f"Key status: {status}")
    
    stored_key_count = status.get("stored_key_count", 0)
    if stored_key_count <= 0:
        logger.warning("No quantum keys available - check KM server")
        return None
    
    # Request encryption key
    payload = {"number": 1}
    response = await client.post(f"/api/v1/keys/{receiver_sae_id}/enc_keys", json=payload)
    response.raise_for_status()
    
    keys_data = response.json()
    keys = keys_data.get("keys", [])
    
    if not keys:
        logger.error("Failed to retrieve encryption key")
        return None
    
    # Return the first key
    key_data = keys[0]
    logger.info(f"Successfully retrieved key with ID: {key_data.get('key_ID')}")
    
    return key_data

async def test_level1_otp():
    """Test Level 1: Quantum One-Time Pad encryption with real quantum keys"""
    print("\n=== Testing Level 1: Quantum One-Time Pad with real quantum keys ===")
    try:
        from app.services.encryption.level1_otp import encrypt_otp, decrypt_otp
        
        content = "This is a Level 1 OTP encrypted message with real quantum security!"
        user_email = "test@example.com"
        
        # Set up certificates for KM client
        root_dir = r"D:\New folder (8)\qumail-secure-email\qkd_kme_server-master\certs"
        km1_client_cert_path = os.path.join(root_dir, "kme-1-local-zone", "client_1_cert.pem")
        km1_client_key_path = os.path.join(root_dir, "kme-1-local-zone", "client_1.key")
        km1_ca_cert_path = os.path.join(root_dir, "kme-1-local-zone", "ca.crt")
        
        # Create SSL context
        ssl_context = await setup_ssl_context(km1_client_cert_path, km1_client_key_path, km1_ca_cert_path)
        
        # Request quantum key from KM server
        print("Requesting quantum key from KM server...")
        async with httpx.AsyncClient(verify=ssl_context, base_url="https://localhost:13000") as client:
            key_data = await request_quantum_key(client, 3)  # Receiver SAE ID 3
            
            if not key_data:
                print("Failed to retrieve quantum key")
                return False
        
        # Extract key and ID from response
        key = key_data.get("key")
        key_id = key_data.get("key_ID")
        
        if not key:
            print("No quantum key in response")
            return False
        
        print("Encrypting with OTP using real quantum key...")
        encrypted_result = await encrypt_otp(content, user_email, qkd_key=base64.b64decode(key))
        
        print(f"Encrypted successfully with algorithm: {encrypted_result['algorithm']}")
        print(f"Encrypted content length: {len(encrypted_result['encrypted_content'])}")
        
        # Add key ID to metadata for consumption tracking
        encrypted_result['metadata']['key_id'] = key_id
        
        print("Decrypting with OTP...")
        # Copy signature to metadata for proper decryption
        metadata = encrypted_result['metadata']
        metadata['signature'] = encrypted_result['signature']
        metadata['public_key'] = encrypted_result.get('metadata', {}).get('public_key')
        
        decrypted_result = await decrypt_otp(
            encrypted_result['encrypted_content'],
            user_email,
            metadata,
            qkd_key=base64.b64decode(key)  # Use same key for test
        )
        
        success = decrypted_result['decrypted_content'] == content
        print(f"Decryption successful: {success}")
        print(f"Decrypted content: {decrypted_result['decrypted_content']}")
        
        # Mark key as consumed
        print("Marking quantum key as consumed...")
        async with httpx.AsyncClient(verify=ssl_context, base_url="https://localhost:13000") as client:
            payload = {"key_id": key_id, "consumed": True}
            response = await client.post("/api/v1/keys/mark_consumed", json=payload)
            if response.status_code == 200:
                print(f"Key {key_id} marked as consumed")
            else:
                print(f"Failed to mark key as consumed: {response.status_code}")
        
        return success
    except Exception as e:
        print(f"Level 1 OTP test failed: {e}")
        traceback.print_exc()
        return False

async def test_level2_aes():
    """Test Level 2: AES-256-GCM encryption with real quantum keys"""
    print("\n=== Testing Level 2: AES-256-GCM with real quantum keys ===")
    try:
        from app.services.encryption.level2_aes import encrypt_aes, decrypt_aes
        
        content = "This is a Level 2 AES encrypted message with real quantum-enhanced key derivation!"
        user_email = "test@example.com"
        
        # Set up certificates for KM client
        root_dir = r"D:\New folder (8)\qumail-secure-email\qkd_kme_server-master\certs"
        km1_client_cert_path = os.path.join(root_dir, "kme-1-local-zone", "client_1_cert.pem")
        km1_client_key_path = os.path.join(root_dir, "kme-1-local-zone", "client_1.key")
        km1_ca_cert_path = os.path.join(root_dir, "kme-1-local-zone", "ca.crt")
        
        # Create SSL context
        ssl_context = await setup_ssl_context(km1_client_cert_path, km1_client_key_path, km1_ca_cert_path)
        
        # Request quantum key from KM server
        print("Requesting quantum key from KM server...")
        async with httpx.AsyncClient(verify=ssl_context, base_url="https://localhost:13000") as client:
            key_data = await request_quantum_key(client, 3)  # Receiver SAE ID 3
            
            if not key_data:
                print("Failed to retrieve quantum key")
                return False
        
        # Extract key and ID from response
        key = key_data.get("key")
        key_id = key_data.get("key_ID")
        
        if not key:
            print("No quantum key in response")
            return False
        
        print("Encrypting with AES using real quantum key for derivation...")
        encrypted_result = await encrypt_aes(content, user_email, qkd_key=base64.b64decode(key))
        
        print(f"Encrypted successfully with algorithm: {encrypted_result['algorithm']}")
        print(f"Encrypted content length: {len(encrypted_result['encrypted_content'])}")
        
        # Add key ID to metadata for consumption tracking
        encrypted_result['metadata']['key_id'] = key_id
        
        print("Decrypting with AES...")
        decrypted_result = await decrypt_aes(
            encrypted_result['encrypted_content'],
            user_email,
            encrypted_result['metadata'],
            qkd_key=base64.b64decode(key)  # Use same key for test
        )
        
        success = decrypted_result['decrypted_content'] == content
        print(f"Decryption successful: {success}")
        print(f"Decrypted content: {decrypted_result['decrypted_content']}")
        
        # Mark key as consumed
        print("Marking quantum key as consumed...")
        async with httpx.AsyncClient(verify=ssl_context, base_url="https://localhost:13000") as client:
            payload = {"key_id": key_id, "consumed": True}
            response = await client.post("/api/v1/keys/mark_consumed", json=payload)
            if response.status_code == 200:
                print(f"Key {key_id} marked as consumed")
            else:
                print(f"Failed to mark key as consumed: {response.status_code}")
        
        return success
    except Exception as e:
        print(f"Level 2 AES test failed: {e}")
        traceback.print_exc()
        return False

async def test_level3_pqc():
    """Test Level 3: Post-Quantum Cryptography with real quantum keys"""
    print("\n=== Testing Level 3: Post-Quantum Cryptography with real quantum keys ===")
    try:
        # Import needed functions
        from app.services.encryption.level3_pqc import is_pqc_available, encrypt_pqc, decrypt_pqc
        
        print(f"PQC Available: {is_pqc_available()}")
        
        content = "This is a Level 3 Post-Quantum encrypted message with real quantum keys!"
        user_email = "test@example.com"
        
        # Set up certificates for KM client
        root_dir = r"D:\New folder (8)\qumail-secure-email\qkd_kme_server-master\certs"
        km1_client_cert_path = os.path.join(root_dir, "kme-1-local-zone", "client_1_cert.pem")
        km1_client_key_path = os.path.join(root_dir, "kme-1-local-zone", "client_1.key")
        km1_ca_cert_path = os.path.join(root_dir, "kme-1-local-zone", "ca.crt")
        
        # Create SSL context
        ssl_context = await setup_ssl_context(km1_client_cert_path, km1_client_key_path, km1_ca_cert_path)
        
        # Request quantum key from KM server
        print("Requesting quantum key from KM server...")
        async with httpx.AsyncClient(verify=ssl_context, base_url="https://localhost:13000") as client:
            key_data = await request_quantum_key(client, 3)  # Receiver SAE ID 3
            
            if not key_data:
                print("Failed to retrieve quantum key")
                return False
        
        # Extract key and ID from response
        key = key_data.get("key")
        key_id = key_data.get("key_ID")
        
        if not key:
            print("No quantum key in response")
            return False
        
        print("Encrypting with PQC using real quantum key for added security...")
        encrypted_result = await encrypt_pqc(content, user_email, qkd_key=base64.b64decode(key))
        
        print(f"Encrypted successfully with algorithm: {encrypted_result['algorithm']}")
        print(f"Encrypted content length: {len(encrypted_result['encrypted_content'])}")
        
        # Add key ID to metadata for consumption tracking
        encrypted_result['metadata']['key_id'] = key_id
        
        print("Decrypting with PQC...")
        decrypted_result = await decrypt_pqc(
            encrypted_result['encrypted_content'],
            user_email,
            encrypted_result['metadata'],
            qkd_key=base64.b64decode(key)  # Use same key for test
        )
        
        success = decrypted_result['decrypted_content'] == content
        print(f"Decryption successful: {success}")
        print(f"Decrypted content: {decrypted_result['decrypted_content']}")
        
        # Mark key as consumed
        print("Marking quantum key as consumed...")
        async with httpx.AsyncClient(verify=ssl_context, base_url="https://localhost:13000") as client:
            payload = {"key_id": key_id, "consumed": True}
            response = await client.post("/api/v1/keys/mark_consumed", json=payload)
            if response.status_code == 200:
                print(f"Key {key_id} marked as consumed")
            else:
                print(f"Failed to mark key as consumed: {response.status_code}")
        
        return success
    except Exception as e:
        print(f"Level 3 PQC test failed: {e}")
        traceback.print_exc()
        return False

async def test_level4_rsa():
    """Test Level 4: Hybrid RSA+AES encryption with real quantum keys"""
    print("\n=== Testing Level 4: Hybrid RSA+AES with real quantum keys ===")
    try:
        from app.services.encryption.level4_rsa import encrypt_rsa, decrypt_rsa
        
        content = "This is a Level 4 RSA+AES hybrid encrypted message with real quantum keys!"
        user_email = "test@example.com"
        
        # Set up certificates for KM client
        root_dir = r"D:\New folder (8)\qumail-secure-email\qkd_kme_server-master\certs"
        km1_client_cert_path = os.path.join(root_dir, "kme-1-local-zone", "client_1_cert.pem")
        km1_client_key_path = os.path.join(root_dir, "kme-1-local-zone", "client_1.key")
        km1_ca_cert_path = os.path.join(root_dir, "kme-1-local-zone", "ca.crt")
        
        # Create SSL context
        ssl_context = await setup_ssl_context(km1_client_cert_path, km1_client_key_path, km1_ca_cert_path)
        
        # Request quantum key from KM server
        print("Requesting quantum key from KM server...")
        async with httpx.AsyncClient(verify=ssl_context, base_url="https://localhost:13000") as client:
            key_data = await request_quantum_key(client, 3)  # Receiver SAE ID 3
            
            if not key_data:
                print("Failed to retrieve quantum key")
                return False
        
        # Extract key and ID from response
        key = key_data.get("key")
        key_id = key_data.get("key_ID")
        
        if not key:
            print("No quantum key in response")
            return False
        
        print("Encrypting with RSA+AES using real quantum key for enhanced security...")
        encrypted_result = await encrypt_rsa(content, user_email, qkd_key=base64.b64decode(key))
        
        print(f"Encrypted successfully with algorithm: {encrypted_result['algorithm']}")
        print(f"Encrypted content length: {len(encrypted_result['encrypted_content'])}")
        
        # Add key ID to metadata for consumption tracking
        encrypted_result['metadata']['key_id'] = key_id
        
        # Fix: Ensure signature is copied to metadata for decryption
        if 'signature' in encrypted_result and 'signature' not in encrypted_result['metadata']:
            encrypted_result['metadata']['signature'] = encrypted_result['signature']
        
        print("Decrypting with RSA+AES...")
        decrypted_result = await decrypt_rsa(
            encrypted_result['encrypted_content'],
            user_email,
            encrypted_result['metadata'],
            qkd_key=base64.b64decode(key)  # Use same key for test
        )
        
        success = decrypted_result['decrypted_content'] == content
        print(f"Decryption successful: {success}")
        print(f"Decrypted content: {decrypted_result['decrypted_content']}")
        
        # Mark key as consumed
        print("Marking quantum key as consumed...")
        async with httpx.AsyncClient(verify=ssl_context, base_url="https://localhost:13000") as client:
            payload = {"key_id": key_id, "consumed": True}
            response = await client.post("/api/v1/keys/mark_consumed", json=payload)
            if response.status_code == 200:
                print(f"Key {key_id} marked as consumed")
            else:
                print(f"Failed to mark key as consumed: {response.status_code}")
        
        return success
    except Exception as e:
        print(f"Level 4 RSA test failed: {e}")
        traceback.print_exc()
        return False

async def test_km_server_connection():
    """Test connection to KM servers before starting encryption tests"""
    print("\n=== Testing connection to KM servers ===")
    
    # Set up certificates for KM client
    root_dir = r"D:\New folder (8)\qumail-secure-email\qkd_kme_server-master\certs"
    
    # Alice's certificates (KME 1)
    km1_client_cert_path = os.path.join(root_dir, "kme-1-local-zone", "client_1_cert.pem")
    km1_client_key_path = os.path.join(root_dir, "kme-1-local-zone", "client_1.key")
    km1_ca_cert_path = os.path.join(root_dir, "kme-1-local-zone", "ca.crt")
    
    # Bob's certificates (KME 2)
    km2_client_cert_path = os.path.join(root_dir, "kme-2-local-zone", "client_3_cert.pem")
    km2_client_key_path = os.path.join(root_dir, "kme-2-local-zone", "client_3.key")
    km2_ca_cert_path = os.path.join(root_dir, "kme-2-local-zone", "ca.crt")
    
    try:
        # Test connection to KME 1 (Alice)
        km1_ssl_context = await setup_ssl_context(
            km1_client_cert_path, 
            km1_client_key_path, 
            km1_ca_cert_path
        )
        
        print("Testing connection to KME 1 (Alice)...")
        async with httpx.AsyncClient(verify=km1_ssl_context, base_url="https://localhost:13000") as client:
            response = await client.get("/api/v1/sae/info/me")
            response.raise_for_status()
            print(f"KME 1 SAE info: {response.text}")
            
            # Check key status with receiver
            response = await client.get("/api/v1/keys/3/status")  # Receiver SAE ID 3
            response.raise_for_status()
            key_status = response.json()
            print(f"KME 1 key status with receiver: {key_status}")
            
            if key_status.get("stored_key_count", 0) <= 0:
                print("WARNING: No quantum keys available in KME 1")
                return False
        
        # Test connection to KME 2 (Bob)
        km2_ssl_context = await setup_ssl_context(
            km2_client_cert_path, 
            km2_client_key_path, 
            km2_ca_cert_path
        )
        
        print("Testing connection to KME 2 (Bob)...")
        async with httpx.AsyncClient(verify=km2_ssl_context, base_url="https://localhost:14000") as client:
            response = await client.get("/api/v1/sae/info/me")
            response.raise_for_status()
            print(f"KME 2 SAE info: {response.text}")
            
            # Check key status with sender
            response = await client.get("/api/v1/keys/1/status")  # Sender SAE ID 1
            response.raise_for_status()
            key_status = response.json()
            print(f"KME 2 key status with sender: {key_status}")
            
            if key_status.get("stored_key_count", 0) <= 0:
                print("WARNING: No quantum keys available in KME 2")
                return False
        
        return True
    except Exception as e:
        print(f"KM server connection test failed: {e}")
        traceback.print_exc()
        return False

async def main():
    """Run encryption tests with real KM servers"""
    print("="*80)
    print("  QUMAIL SECURE EMAIL - ENCRYPTION LEVELS TEST WITH REAL QUANTUM KEYS")
    print("  (Connecting to real KM servers for quantum key distribution)")
    print("="*80)
    
    results = {}
    
    # First test KM server connection
    results["KM Server Connection"] = await test_km_server_connection()
    
    # Only continue with encryption tests if KM server connection succeeded
    if results["KM Server Connection"]:
        # Test all four encryption levels
        results["Level 1: Quantum OTP"] = await test_level1_otp()
        results["Level 2: AES-256-GCM"] = await test_level2_aes()
        results["Level 3: Post-Quantum"] = await test_level3_pqc()
        results["Level 4: RSA+AES"] = await test_level4_rsa()
    
    # Print results summary
    print("\n" + "="*50)
    print("  TEST RESULTS SUMMARY")
    print("="*50)
    
    all_passed = True
    for name, success in results.items():
        status = "PASSED" if success else "FAILED"
        all_passed = all_passed and success
        print(f"{name}: {status}")
    
    print("\n" + "="*50)
    print(f"  OVERALL TEST STATUS: {'PASSED' if all_passed else 'FAILED'}")
    print("="*50)
    
    return all_passed

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)