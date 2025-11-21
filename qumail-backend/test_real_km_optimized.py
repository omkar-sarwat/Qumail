#!/usr/bin/env python
"""
Test script for optimized KM client that reliably connects to real quantum key servers.
This script tests the improved client with longer timeouts, retry logic, and key caching.
"""

import os
import sys
import logging
import base64
import asyncio
import ssl
import httpx
import json
import time
import traceback
from typing import Dict, Any, List, Union
import uuid

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ensure we can import from the app package
sys.path.append(os.path.dirname(__file__))

# Import the required modules
from app.config import get_settings
from app.services.optimized_km_client import OptimizedKMClient, create_optimized_km_clients

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
        async with httpx.AsyncClient(verify=km1_ssl_context, base_url="https://localhost:13000", timeout=30.0) as client:
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
        async with httpx.AsyncClient(verify=km2_ssl_context, base_url="https://localhost:14000", timeout=30.0) as client:
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

async def test_optimized_km_client_connection():
    """Test the optimized KM client connection"""
    print("\n=== Testing Optimized KM Client Connection ===")
    
    try:
        # Create optimized KM clients
        km1_client, km2_client = create_optimized_km_clients()
        
        # Test Alice's KM client (KME 1)
        print("Testing Alice's KM client...")
        alice_info = await km1_client.get_sae_info()
        print(f"Alice SAE info: {alice_info}")
        
        alice_status = await km1_client.check_key_status(3)  # Receiver SAE ID 3
        print(f"Alice key status with Bob: {alice_status}")
        
        alice_entropy = await km1_client.check_entropy()
        print(f"Alice KM entropy: {alice_entropy}")
        
        # Test Bob's KM client (KME 2)
        print("\nTesting Bob's KM client...")
        bob_info = await km2_client.get_sae_info()
        print(f"Bob SAE info: {bob_info}")
        
        bob_status = await km2_client.check_key_status(1)  # Sender SAE ID 1
        print(f"Bob key status with Alice: {bob_status}")
        
        bob_entropy = await km2_client.check_entropy()
        print(f"Bob KM entropy: {bob_entropy}")
        
        # Close clients
        await km1_client.close()
        await km2_client.close()
        
        return True
    except Exception as e:
        print(f"Optimized KM client connection test failed: {e}")
        traceback.print_exc()
        return False

async def test_key_request_with_retry():
    """Test requesting keys with retry logic"""
    print("\n=== Testing Key Request with Retry Logic ===")
    
    try:
        # Create optimized KM clients
        km1_client, km2_client = create_optimized_km_clients()
        
        # Check key status
        status = await km1_client.check_key_status(3)  # Receiver SAE ID 3
        available_keys = status.get('stored_key_count', 0)
        print(f"Available keys: {available_keys}")
        
        if available_keys <= 0:
            print("No keys available for testing!")
            return False
        
        # Request a key (this will use retry logic if needed)
        print("Requesting an encryption key (this may take time due to retries)...")
        keys = await km1_client.request_enc_keys(3, number=1)
        
        if not keys:
            print("Failed to retrieve keys even with retry logic!")
            return False
        
        print(f"Successfully retrieved {len(keys)} keys")
        print(f"Key ID: {keys[0].get('key_ID')}")
        
        # Test key cache population
        print("\nTesting key cache population...")
        print("Requesting multiple keys to populate cache...")
        
        start_time = time.time()
        keys = await km1_client.request_enc_keys(3, number=3)
        elapsed = time.time() - start_time
        
        print(f"Retrieved {len(keys)} keys in {elapsed:.2f} seconds")
        
        # Request again - should be faster with cache
        print("\nRequesting keys again (should be faster with cache)...")
        start_time = time.time()
        cached_keys = await km1_client.request_enc_keys(3, number=2)
        cached_elapsed = time.time() - start_time
        
        print(f"Retrieved {len(cached_keys)} keys in {cached_elapsed:.2f} seconds")
        print(f"Cache speedup: {elapsed/cached_elapsed:.2f}x faster")
        
        # Close clients
        await km1_client.close()
        await km2_client.close()
        
        return len(cached_keys) > 0
    except Exception as e:
        print(f"Key request test failed: {e}")
        traceback.print_exc()
        return False

async def test_key_consumption_tracking():
    """Test key consumption tracking"""
    print("\n=== Testing Key Consumption Tracking ===")
    
    try:
        # Create optimized KM clients
        km1_client, km2_client = create_optimized_km_clients()
        
        # Request keys
        keys = await km1_client.request_enc_keys(3, number=2)
        
        if not keys or len(keys) < 2:
            print("Failed to retrieve enough keys for testing!")
            return False
        
        key1_id = keys[0].get('key_ID')
        key2_id = keys[1].get('key_ID')
        
        print(f"Retrieved keys with IDs: {key1_id}, {key2_id}")
        
        # Mark first key as consumed
        print(f"Marking key {key1_id} as consumed...")
        consumed = await km1_client.mark_key_consumed(key1_id)
        print(f"Key {key1_id} marked as consumed: {consumed}")
        
        # Check if keys are tracked as consumed
        print("Verifying consumed key tracking...")
        
        # Request a key - should not return the consumed one
        new_keys = await km1_client.request_enc_keys(3, number=1)
        new_key_id = new_keys[0].get('key_ID')
        
        print(f"New key ID: {new_key_id}")
        
        # Verify the consumed key is not returned
        if new_key_id == key1_id:
            print("ERROR: Consumed key was returned again!")
            return False
        
        print("Key consumption tracking is working correctly")
        
        # Close clients
        await km1_client.close()
        await km2_client.close()
        
        return True
    except Exception as e:
        print(f"Key consumption tracking test failed: {e}")
        traceback.print_exc()
        return False

async def test_encryption_with_real_km():
    """Test encryption with real KM keys"""
    print("\n=== Testing Encryption with Real KM Keys ===")
    
    try:
        from app.services.encryption.level1_otp import encrypt_otp, decrypt_otp
        
        # Create optimized KM clients
        km1_client, km2_client = create_optimized_km_clients()
        
        content = "This is a Level 1 OTP encrypted message with real quantum keys!"
        user_email = "test@example.com"
        
        # Request an encryption key
        print("Requesting encryption key from KM server...")
        keys = await km1_client.request_enc_keys(3, number=1)
        
        if not keys:
            print("Failed to retrieve keys for encryption!")
            return False
        
        key_id = keys[0].get('key_ID')
        key_data = base64.b64decode(keys[0].get('key'))
        
        print(f"Retrieved key ID: {key_id}")
        
        # Encrypt with OTP using real quantum key
        print("Encrypting with OTP using real quantum key...")
        encrypted_result = await encrypt_otp(content, user_email, qkd_key=key_data)
        
        print(f"Encrypted successfully with algorithm: {encrypted_result['algorithm']}")
        print(f"Encrypted content length: {len(encrypted_result['encrypted_content'])}")
        
        # Add key ID to metadata for tracking
        encrypted_result['metadata']['key_id'] = key_id
        
        # Copy signature to metadata for proper decryption
        metadata = encrypted_result['metadata']
        metadata['signature'] = encrypted_result['signature']
        metadata['public_key'] = encrypted_result.get('metadata', {}).get('public_key')
        
        # Request the same key for decryption
        print("Requesting decryption key...")
        dec_keys = await km2_client.request_dec_keys(1, [key_id])
        
        if not dec_keys:
            print("Failed to retrieve decryption key!")
            return False
        
        dec_key_data = base64.b64decode(dec_keys[0].get('key'))
        
        print("Decrypting with OTP using real quantum key...")
        decrypted_result = await decrypt_otp(
            encrypted_result['encrypted_content'],
            user_email,
            metadata,
            qkd_key=dec_key_data
        )
        
        success = decrypted_result['decrypted_content'] == content
        print(f"Decryption successful: {success}")
        print(f"Decrypted content: {decrypted_result['decrypted_content']}")
        
        # Mark key as consumed
        print(f"Marking key {key_id} as consumed...")
        await km1_client.mark_key_consumed(key_id)
        await km2_client.mark_key_consumed(key_id)
        
        # Close clients
        await km1_client.close()
        await km2_client.close()
        
        return success
    except Exception as e:
        print(f"Encryption test with real KM failed: {e}")
        traceback.print_exc()
        return False

async def test_all_encryption_levels():
    """Test all encryption levels with real KM keys"""
    print("\n=== Testing All Encryption Levels with Real KM ===")
    
    # Create optimized KM clients
    km1_client, km2_client = create_optimized_km_clients()
    
    results = {}
    
    try:
        # Test Level 1: OTP
        from app.services.encryption.level1_otp import encrypt_otp, decrypt_otp
        
        print("\n--- Testing Level 1: Quantum OTP ---")
        content = "This is a Level 1 OTP encrypted message with real quantum keys!"
        user_email = "test@example.com"
        
        # Request a key
        keys = await km1_client.request_enc_keys(3, number=1)
        if not keys:
            print("Failed to retrieve keys for Level 1 encryption!")
            results["Level 1: OTP"] = False
        else:
            key_id = keys[0].get('key_ID')
            key_data = base64.b64decode(keys[0].get('key'))
            
            # Encrypt
            encrypted_result = await encrypt_otp(content, user_email, qkd_key=key_data)
            encrypted_result['metadata']['key_id'] = key_id
            metadata = encrypted_result['metadata']
            metadata['signature'] = encrypted_result['signature']
            
            # Decrypt
            dec_keys = await km2_client.request_dec_keys(1, [key_id])
            if not dec_keys:
                print("Failed to retrieve decryption key for Level 1!")
                results["Level 1: OTP"] = False
            else:
                dec_key_data = base64.b64decode(dec_keys[0].get('key'))
                decrypted_result = await decrypt_otp(
                    encrypted_result['encrypted_content'],
                    user_email,
                    metadata,
                    qkd_key=dec_key_data
                )
                
                success = decrypted_result['decrypted_content'] == content
                print(f"Level 1 decryption successful: {success}")
                results["Level 1: OTP"] = success
                
                # Mark key as consumed
                await km1_client.mark_key_consumed(key_id)
                await km2_client.mark_key_consumed(key_id)
    except Exception as e:
        print(f"Level 1 encryption test failed: {e}")
        results["Level 1: OTP"] = False
    
    try:
        # Test Level 2: AES-GCM
        from app.services.encryption.level2_aes import encrypt_aes, decrypt_aes
        
        print("\n--- Testing Level 2: AES-256-GCM ---")
        content = "This is a Level 2 AES encrypted message with real quantum keys!"
        user_email = "test@example.com"
        
        # Request a key
        keys = await km1_client.request_enc_keys(3, number=1)
        if not keys:
            print("Failed to retrieve keys for Level 2 encryption!")
            results["Level 2: AES-GCM"] = False
        else:
            key_id = keys[0].get('key_ID')
            key_data = base64.b64decode(keys[0].get('key'))
            
            # Encrypt
            encrypted_result = await encrypt_aes(content, user_email, qkd_key=key_data)
            encrypted_result['metadata']['key_id'] = key_id
            
            # Decrypt
            dec_keys = await km2_client.request_dec_keys(1, [key_id])
            if not dec_keys:
                print("Failed to retrieve decryption key for Level 2!")
                results["Level 2: AES-GCM"] = False
            else:
                dec_key_data = base64.b64decode(dec_keys[0].get('key'))
                decrypted_result = await decrypt_aes(
                    encrypted_result['encrypted_content'],
                    user_email,
                    encrypted_result['metadata'],
                    qkd_key=dec_key_data
                )
                
                success = decrypted_result['decrypted_content'] == content
                print(f"Level 2 decryption successful: {success}")
                results["Level 2: AES-GCM"] = success
                
                # Mark key as consumed
                await km1_client.mark_key_consumed(key_id)
                await km2_client.mark_key_consumed(key_id)
    except Exception as e:
        print(f"Level 2 encryption test failed: {e}")
        results["Level 2: AES-GCM"] = False
    
    try:
        # Test Level 3: PQC
        from app.services.encryption.level3_pqc import encrypt_pqc, decrypt_pqc, is_pqc_available
        
        print("\n--- Testing Level 3: Post-Quantum Cryptography ---")
        print(f"PQC available: {is_pqc_available()}")
        
        if not is_pqc_available():
            print("PQC not available, skipping Level 3 test")
            results["Level 3: PQC"] = None
        else:
            content = "This is a Level 3 PQC encrypted message with real quantum keys!"
            user_email = "test@example.com"
            
            # Request a key
            keys = await km1_client.request_enc_keys(3, number=1)
            if not keys:
                print("Failed to retrieve keys for Level 3 encryption!")
                results["Level 3: PQC"] = False
            else:
                key_id = keys[0].get('key_ID')
                key_data = base64.b64decode(keys[0].get('key'))
                
                # Encrypt
                encrypted_result = await encrypt_pqc(content, user_email, qkd_key=key_data)
                encrypted_result['metadata']['key_id'] = key_id
                
                # Decrypt
                dec_keys = await km2_client.request_dec_keys(1, [key_id])
                if not dec_keys:
                    print("Failed to retrieve decryption key for Level 3!")
                    results["Level 3: PQC"] = False
                else:
                    dec_key_data = base64.b64decode(dec_keys[0].get('key'))
                    decrypted_result = await decrypt_pqc(
                        encrypted_result['encrypted_content'],
                        user_email,
                        encrypted_result['metadata'],
                        qkd_key=dec_key_data
                    )
                    
                    success = decrypted_result['decrypted_content'] == content
                    print(f"Level 3 decryption successful: {success}")
                    results["Level 3: PQC"] = success
                    
                    # Mark key as consumed
                    await km1_client.mark_key_consumed(key_id)
                    await km2_client.mark_key_consumed(key_id)
    except Exception as e:
        print(f"Level 3 encryption test failed: {e}")
        results["Level 3: PQC"] = False
    
    try:
        # Test Level 4: RSA+AES
        from app.services.encryption.level4_rsa import encrypt_rsa, decrypt_rsa
        
        print("\n--- Testing Level 4: RSA+AES Hybrid ---")
        content = "This is a Level 4 RSA+AES hybrid encrypted message with real quantum keys!"
        user_email = "test@example.com"
        
        # Request a key
        keys = await km1_client.request_enc_keys(3, number=1)
        if not keys:
            print("Failed to retrieve keys for Level 4 encryption!")
            results["Level 4: RSA+AES"] = False
        else:
            key_id = keys[0].get('key_ID')
            key_data = base64.b64decode(keys[0].get('key'))
            
            # Encrypt
            encrypted_result = await encrypt_rsa(content, user_email, qkd_key=key_data)
            encrypted_result['metadata']['key_id'] = key_id
            
            # Fix: Ensure signature is copied to metadata for decryption
            if 'signature' in encrypted_result and 'signature' not in encrypted_result['metadata']:
                encrypted_result['metadata']['signature'] = encrypted_result['signature']
            
            # Decrypt
            dec_keys = await km2_client.request_dec_keys(1, [key_id])
            if not dec_keys:
                print("Failed to retrieve decryption key for Level 4!")
                results["Level 4: RSA+AES"] = False
            else:
                dec_key_data = base64.b64decode(dec_keys[0].get('key'))
                decrypted_result = await decrypt_rsa(
                    encrypted_result['encrypted_content'],
                    user_email,
                    encrypted_result['metadata'],
                    qkd_key=dec_key_data
                )
                
                success = decrypted_result['decrypted_content'] == content
                print(f"Level 4 decryption successful: {success}")
                results["Level 4: RSA+AES"] = success
                
                # Mark key as consumed
                await km1_client.mark_key_consumed(key_id)
                await km2_client.mark_key_consumed(key_id)
    except Exception as e:
        print(f"Level 4 encryption test failed: {e}")
        results["Level 4: RSA+AES"] = False
    
    # Close clients
    await km1_client.close()
    await km2_client.close()
    
    return results

async def main():
    """Run tests for optimized KM client"""
    print("="*80)
    print("  QUMAIL SECURE EMAIL - REAL KM SERVER TESTING")
    print("  (With optimized KM client and real quantum keys)")
    print("="*80)
    
    results = {}
    
    # First verify KM server connection
    results["KM Server Connection"] = await verify_km_connection()
    
    # Only continue with KM client tests if KM server connection succeeded
    if results["KM Server Connection"]:
        # Test optimized KM client connection
        results["Optimized KM Client Connection"] = await test_optimized_km_client_connection()
        
        # Test key request with retry logic
        results["Key Request with Retry"] = await test_key_request_with_retry()
        
        # Test key consumption tracking
        results["Key Consumption Tracking"] = await test_key_consumption_tracking()
        
        # Test encryption with real KM
        results["Encryption with Real KM"] = await test_encryption_with_real_km()
        
        # Test all encryption levels
        print("\n=== Testing All Encryption Levels ===")
        encryption_results = await test_all_encryption_levels()
        results.update(encryption_results)
    
    # Print results summary
    print("\n" + "="*50)
    print("  TEST RESULTS SUMMARY")
    print("="*50)
    
    all_passed = True
    for name, success in results.items():
        if success is None:
            status = "SKIPPED"
        else:
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