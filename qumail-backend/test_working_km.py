#!/usr/bin/env python
"""
Test script for KM client that only uses working endpoints to validate connectivity.
This script avoids the problematic POST requests that lead to 504 Gateway Timeout errors.
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
    """Verify connection to KM servers"""
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
        
        print("\nTesting connection to KME 2 (Bob)...")
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
        return False

async def test_raw_key_fallback():
    """Test using raw key files as fallback when KM server POST requests fail"""
    print("\n=== Testing Raw Key Fallback ===")
    
    from app.services.real_qkd_client import RealQKDClient
    
    try:
        # Initialize the RealQKDClient to test raw key file fallback
        qkd_client = RealQKDClient("kme-1-local-zone", 1)
        
        # Test getting raw keys for encryption
        print("Testing raw key retrieval for encryption...")
        sender_id = 1
        receiver_id = 3
        
        # Get raw keys directly from files
        keys = qkd_client.get_raw_keys(sender_id, receiver_id)
        
        if keys and len(keys) > 0:
            print(f"Successfully retrieved {len(keys)} raw keys")
            first_key = keys[0]
            print(f"First key ID: {first_key[:8]}...")
            print(f"Key size: {len(first_key)} bytes")
            
            # Test if these keys can be used for encryption
            from app.services.encryption.level1_otp import encrypt_otp
            
            sample_content = "This is a test message encrypted with raw quantum key."
            user_email = "test@example.com"
            
            print("\nTesting encryption with raw quantum key...")
            encrypted = await encrypt_otp(sample_content, user_email, qkd_key=first_key)
            
            if encrypted:
                print("✓ Successfully encrypted message with raw quantum key")
                print(f"Algorithm: {encrypted['algorithm']}")
                print(f"Metadata: {encrypted['metadata']}")
                print(f"Encrypted content length: {len(encrypted['encrypted_content'])}")
                
                # Test decryption
                from app.services.encryption.level1_otp import decrypt_otp
                
                print("\nTesting decryption with raw quantum key...")
                # Copy signature to metadata for proper decryption
                metadata = encrypted['metadata']
                metadata['signature'] = encrypted['signature']
                
                decrypted = await decrypt_otp(
                    encrypted['encrypted_content'], 
                    user_email, 
                    metadata, 
                    qkd_key=first_key
                )
                
                if decrypted and decrypted['decrypted_content'] == sample_content:
                    print("✓ Successfully decrypted message with raw quantum key")
                    print(f"Decrypted content: {decrypted['decrypted_content']}")
                    return True
                else:
                    print("✗ Failed to decrypt message with raw quantum key")
                    return False
            else:
                print("✗ Failed to encrypt message with raw quantum key")
                return False
        else:
            print("✗ No raw keys found")
            return False
            
    except Exception as e:
        print(f"Raw key fallback test failed: {e}")
        return False

async def test_hybrid_approach():
    """Test a hybrid approach using GET requests for keys and fallback to raw keys"""
    print("\n=== Testing Hybrid Approach ===")
    
    try:
        # Get KM client instances
        km1_client, km2_client = create_optimized_km_clients()
        
        # Get status information (works with GET requests)
        print("Getting KME status information...")
        alice_info = await km1_client.get_sae_info()
        print(f"Alice SAE info: {alice_info}")
        
        alice_status = await km1_client.check_key_status(3)
        print(f"Alice key status with Bob: {alice_status}")
        
        # Try using RealQKDClient as a fallback
        print("\nFalling back to raw key files...")
        from app.services.real_qkd_client import RealQKDClient
        qkd_client = RealQKDClient("kme-1-local-zone", 1)
        
        keys = qkd_client.get_raw_keys(1, 3)
        if keys and len(keys) > 0:
            print(f"Found {len(keys)} raw keys as fallback")
            
            # Test encryption with the raw key
            from app.services.encryption.level1_otp import encrypt_otp, decrypt_otp
            
            # Encrypt test message
            sample_content = "This is a hybrid approach using KME status and raw key files."
            user_email = "test@example.com"
            
            # Use first raw key
            key_data = keys[0]  # Already in bytes format
            encrypted = await encrypt_otp(sample_content, user_email, qkd_key=key_data)
            
            if encrypted:
                print("✓ Successfully encrypted with hybrid approach")
                
                # Prepare metadata for decryption
                metadata = encrypted['metadata']
                metadata['signature'] = encrypted['signature']
                
                # Decrypt using the same key
                decrypted = await decrypt_otp(
                    encrypted['encrypted_content'],
                    user_email,
                    metadata,
                    qkd_key=key_data
                )
                
                if decrypted and decrypted['decrypted_content'] == sample_content:
                    print("✓ Successfully decrypted with hybrid approach")
                    print(f"Decrypted content: {decrypted['decrypted_content']}")
                    return True
                else:
                    print("✗ Failed to decrypt with hybrid approach")
                    return False
            else:
                print("✗ Failed to encrypt with hybrid approach")
                return False
        else:
            print("✗ No raw keys found for fallback")
            return False
            
    except Exception as e:
        print(f"Hybrid approach test failed: {e}")
        return False
    finally:
        # Close KM clients
        await km1_client.close()
        await km2_client.close()

async def main():
    """Run tests for KM clients with focus on working endpoints"""
    print("="*80)
    print("  QUMAIL SECURE EMAIL - KM CONNECTIVITY TESTING")
    print("  (Focusing on working endpoints)")
    print("="*80)
    
    results = {}
    
    # Verify KM server connections
    results["KM Server Connection"] = await verify_km_connection()
    
    # Test raw key fallback
    results["Raw Key Fallback"] = await test_raw_key_fallback()
    
    # Test hybrid approach
    results["Hybrid Approach"] = await test_hybrid_approach()
    
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