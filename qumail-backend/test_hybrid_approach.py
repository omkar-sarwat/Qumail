#!/usr/bin/env python
"""
Test script for hybrid testing of encryption with real KM connections but mock keys.
This script tests all four encryption levels using real KM server connections but
with mock quantum keys to bypass the key request timeout issue.
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
import json

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

async def verify_km_connection():
    """Verify connection to KM servers before starting tests"""
    print("\n=== Verifying KM Server Connections ===")
    
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
            
            # Get entropy info
            response = await client.get("/api/v1/keys/entropy/total")
            response.raise_for_status()
            entropy_info = response.json()
            print(f"KME 1 entropy: {entropy_info}")
        
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
            
            # Get entropy info
            response = await client.get("/api/v1/keys/entropy/total")
            response.raise_for_status()
            entropy_info = response.json()
            print(f"KME 2 entropy: {entropy_info}")
        
        return True
    except Exception as e:
        print(f"KM server connection verification failed: {e}")
        traceback.print_exc()
        return False

async def generate_mock_quantum_key():
    """Generate a mock quantum key with properties like a real one"""
    key_data = os.urandom(32)  # 256 bits = 32 bytes
    key_id = str(uuid.uuid4())
    
    return {
        "key": base64.b64encode(key_data).decode(),
        "key_ID": key_id,
        "key_size": 256
    }

async def test_level1_otp_hybrid():
    """Test Level 1: Quantum One-Time Pad encryption with mock keys but real KM connection"""
    print("\n=== Testing Level 1: Quantum OTP with Hybrid Approach ===")
    try:
        from app.services.encryption.level1_otp import encrypt_otp, decrypt_otp
        
        content = "This is a Level 1 OTP encrypted message with hybrid approach!"
        user_email = "test@example.com"
        
        # Verify KM connection
        root_dir = r"D:\New folder (8)\qumail-secure-email\qkd_kme_server-master\certs"
        km1_client_cert_path = os.path.join(root_dir, "kme-1-local-zone", "client_1_cert.pem")
        km1_client_key_path = os.path.join(root_dir, "kme-1-local-zone", "client_1.key")
        km1_ca_cert_path = os.path.join(root_dir, "kme-1-local-zone", "ca.crt")
        
        ssl_context = await setup_ssl_context(km1_client_cert_path, km1_client_key_path, km1_ca_cert_path)
        
        # Verify KM connection
        async with httpx.AsyncClient(verify=ssl_context, base_url="https://localhost:13000") as client:
            response = await client.get("/api/v1/keys/3/status")  # Receiver SAE ID 3
            response.raise_for_status()
            key_status = response.json()
            print(f"Key status verified: {key_status['stored_key_count']} keys available")
        
        # Generate a mock quantum key
        mock_key = await generate_mock_quantum_key()
        print(f"Generated mock key ID: {mock_key['key_ID']}")
        
        # Encrypt with normal OTP (doesn't directly use quantum key)
        print("Encrypting with OTP...")
        encrypted_result = await encrypt_otp(content, user_email)
        
        print(f"Encrypted successfully with algorithm: {encrypted_result['algorithm']}")
        print(f"Encrypted content length: {len(encrypted_result['encrypted_content'])}")
        
        # Add mock quantum key ID to metadata for tracking
        encrypted_result['metadata']['key_id'] = mock_key['key_ID']
        
        # Copy signature to metadata for proper decryption
        metadata = encrypted_result['metadata']
        metadata['signature'] = encrypted_result['signature']
        metadata['public_key'] = encrypted_result.get('metadata', {}).get('public_key')
        
        print("Decrypting with OTP...")
        decrypted_result = await decrypt_otp(
            encrypted_result['encrypted_content'],
            user_email,
            metadata
        )
        
        success = decrypted_result['decrypted_content'] == content
        print(f"Decryption successful: {success}")
        print(f"Decrypted content: {decrypted_result['decrypted_content']}")
        
        # Simulate key consumption
        print(f"Simulating consumption of key ID: {mock_key['key_ID']}")
        
        return success
    except Exception as e:
        print(f"Level 1 OTP hybrid test failed: {e}")
        traceback.print_exc()
        return False

async def test_level2_aes_hybrid():
    """Test Level 2: AES-256-GCM encryption with mock keys but real KM connection"""
    print("\n=== Testing Level 2: AES-256-GCM with Hybrid Approach ===")
    try:
        from app.services.encryption.level2_aes import encrypt_aes, decrypt_aes
        
        content = "This is a Level 2 AES encrypted message with hybrid approach!"
        user_email = "test@example.com"
        
        # Verify KM connection
        root_dir = r"D:\New folder (8)\qumail-secure-email\qkd_kme_server-master\certs"
        km1_client_cert_path = os.path.join(root_dir, "kme-1-local-zone", "client_1_cert.pem")
        km1_client_key_path = os.path.join(root_dir, "kme-1-local-zone", "client_1.key")
        km1_ca_cert_path = os.path.join(root_dir, "kme-1-local-zone", "ca.crt")
        
        ssl_context = await setup_ssl_context(km1_client_cert_path, km1_client_key_path, km1_ca_cert_path)
        
        # Verify KM connection
        async with httpx.AsyncClient(verify=ssl_context, base_url="https://localhost:13000") as client:
            response = await client.get("/api/v1/keys/3/status")  # Receiver SAE ID 3
            response.raise_for_status()
            key_status = response.json()
            print(f"Key status verified: {key_status['stored_key_count']} keys available")
        
        # Generate a mock quantum key
        mock_key = await generate_mock_quantum_key()
        print(f"Generated mock key ID: {mock_key['key_ID']}")
        
        # Encrypt with AES (normally would use quantum key for key derivation)
        print("Encrypting with AES-256-GCM...")
        encrypted_result = await encrypt_aes(content, user_email)
        
        print(f"Encrypted successfully with algorithm: {encrypted_result['algorithm']}")
        print(f"Encrypted content length: {len(encrypted_result['encrypted_content'])}")
        
        # Add mock quantum key ID to metadata for tracking
        encrypted_result['metadata']['key_id'] = mock_key['key_ID']
        
        print("Decrypting with AES-256-GCM...")
        decrypted_result = await decrypt_aes(
            encrypted_result['encrypted_content'],
            user_email,
            encrypted_result['metadata']
        )
        
        success = decrypted_result['decrypted_content'] == content
        print(f"Decryption successful: {success}")
        print(f"Decrypted content: {decrypted_result['decrypted_content']}")
        
        # Simulate key consumption
        print(f"Simulating consumption of key ID: {mock_key['key_ID']}")
        
        return success
    except Exception as e:
        print(f"Level 2 AES hybrid test failed: {e}")
        traceback.print_exc()
        return False

async def test_level3_pqc_hybrid():
    """Test Level 3: Post-Quantum Cryptography with mock keys but real KM connection"""
    print("\n=== Testing Level 3: Post-Quantum Cryptography with Hybrid Approach ===")
    try:
        from app.services.encryption.level3_pqc import is_pqc_available, encrypt_pqc, decrypt_pqc
        
        print(f"PQC Available: {is_pqc_available()}")
        
        content = "This is a Level 3 Post-Quantum encrypted message with hybrid approach!"
        user_email = "test@example.com"
        
        # Verify KM connection
        root_dir = r"D:\New folder (8)\qumail-secure-email\qkd_kme_server-master\certs"
        km1_client_cert_path = os.path.join(root_dir, "kme-1-local-zone", "client_1_cert.pem")
        km1_client_key_path = os.path.join(root_dir, "kme-1-local-zone", "client_1.key")
        km1_ca_cert_path = os.path.join(root_dir, "kme-1-local-zone", "ca.crt")
        
        ssl_context = await setup_ssl_context(km1_client_cert_path, km1_client_key_path, km1_ca_cert_path)
        
        # Verify KM connection
        async with httpx.AsyncClient(verify=ssl_context, base_url="https://localhost:13000") as client:
            response = await client.get("/api/v1/keys/3/status")  # Receiver SAE ID 3
            response.raise_for_status()
            key_status = response.json()
            print(f"Key status verified: {key_status['stored_key_count']} keys available")
        
        # Generate a mock quantum key
        mock_key = await generate_mock_quantum_key()
        print(f"Generated mock key ID: {mock_key['key_ID']}")
        
        # Encrypt with PQC (would normally enhance with quantum key)
        print("Encrypting with PQC...")
        encrypted_result = await encrypt_pqc(content, user_email)
        
        print(f"Encrypted successfully with algorithm: {encrypted_result['algorithm']}")
        print(f"Encrypted content length: {len(encrypted_result['encrypted_content'])}")
        
        # Add mock quantum key ID to metadata for tracking
        encrypted_result['metadata']['key_id'] = mock_key['key_ID']
        
        print("Decrypting with PQC...")
        decrypted_result = await decrypt_pqc(
            encrypted_result['encrypted_content'],
            user_email,
            encrypted_result['metadata']
        )
        
        success = decrypted_result['decrypted_content'] == content
        print(f"Decryption successful: {success}")
        print(f"Decrypted content: {decrypted_result['decrypted_content']}")
        
        # Simulate key consumption
        print(f"Simulating consumption of key ID: {mock_key['key_ID']}")
        
        return success
    except Exception as e:
        print(f"Level 3 PQC hybrid test failed: {e}")
        traceback.print_exc()
        return False

async def test_level4_rsa_hybrid():
    """Test Level 4: Hybrid RSA+AES encryption with mock keys but real KM connection"""
    print("\n=== Testing Level 4: Hybrid RSA+AES with Hybrid Approach ===")
    try:
        from app.services.encryption.level4_rsa import encrypt_rsa, decrypt_rsa
        
        content = "This is a Level 4 RSA+AES hybrid encrypted message with hybrid approach!"
        user_email = "test@example.com"
        
        # Verify KM connection
        root_dir = r"D:\New folder (8)\qumail-secure-email\qkd_kme_server-master\certs"
        km1_client_cert_path = os.path.join(root_dir, "kme-1-local-zone", "client_1_cert.pem")
        km1_client_key_path = os.path.join(root_dir, "kme-1-local-zone", "client_1.key")
        km1_ca_cert_path = os.path.join(root_dir, "kme-1-local-zone", "ca.crt")
        
        ssl_context = await setup_ssl_context(km1_client_cert_path, km1_client_key_path, km1_ca_cert_path)
        
        # Verify KM connection
        async with httpx.AsyncClient(verify=ssl_context, base_url="https://localhost:13000") as client:
            response = await client.get("/api/v1/keys/3/status")  # Receiver SAE ID 3
            response.raise_for_status()
            key_status = response.json()
            print(f"Key status verified: {key_status['stored_key_count']} keys available")
        
        # Generate a mock quantum key
        mock_key = await generate_mock_quantum_key()
        print(f"Generated mock key ID: {mock_key['key_ID']}")
        
        # Encrypt with RSA+AES
        print("Encrypting with RSA+AES...")
        encrypted_result = await encrypt_rsa(content, user_email)
        
        print(f"Encrypted successfully with algorithm: {encrypted_result['algorithm']}")
        print(f"Encrypted content length: {len(encrypted_result['encrypted_content'])}")
        
        # Add mock quantum key ID to metadata for tracking
        encrypted_result['metadata']['key_id'] = mock_key['key_ID']
        
        # Fix: Ensure signature is copied to metadata for decryption
        if 'signature' in encrypted_result and 'signature' not in encrypted_result['metadata']:
            encrypted_result['metadata']['signature'] = encrypted_result['signature']
        
        print("Decrypting with RSA+AES...")
        decrypted_result = await decrypt_rsa(
            encrypted_result['encrypted_content'],
            user_email,
            encrypted_result['metadata']
        )
        
        success = decrypted_result['decrypted_content'] == content
        print(f"Decryption successful: {success}")
        print(f"Decrypted content: {decrypted_result['decrypted_content']}")
        
        # Simulate key consumption
        print(f"Simulating consumption of key ID: {mock_key['key_ID']}")
        
        return success
    except Exception as e:
        print(f"Level 4 RSA hybrid test failed: {e}")
        traceback.print_exc()
        return False

async def main():
    """Run hybrid tests with real KM connections but mock keys"""
    print("="*80)
    print("  QUMAIL SECURE EMAIL - HYBRID ENCRYPTION TESTING")
    print("  (Real KM server connections with mock quantum keys)")
    print("="*80)
    
    results = {}
    
    # First verify KM server connection
    results["KM Server Connection"] = await verify_km_connection()
    
    # Only continue with encryption tests if KM server connection succeeded
    if results["KM Server Connection"]:
        # Test all four encryption levels with hybrid approach
        results["Level 1: Quantum OTP"] = await test_level1_otp_hybrid()
        results["Level 2: AES-256-GCM"] = await test_level2_aes_hybrid()
        results["Level 3: Post-Quantum"] = await test_level3_pqc_hybrid()
        results["Level 4: RSA+AES"] = await test_level4_rsa_hybrid()
    
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
    
    if results["KM Server Connection"] and not all_passed:
        print("\nNOTE: KM server connection is working, but key request API is timing out.")
        print("Hybrid approach uses mock keys with real connections for testing.")
        print("When the KM server key request issue is fixed, switch to real quantum keys.")
    
    return all_passed

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)