#!/usr/bin/env python
"""
Test script for connecting to real Quantum Key Management servers with increased timeout.
This script tests key requests with longer timeout values to handle slow server responses.
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
import json

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ensure we can import from the app package
sys.path.append(os.path.dirname(__file__))

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

async def test_key_request_with_timeout():
    """Test key request with increased timeout"""
    print("\n=== Testing key request with increased timeout ===")
    
    # Set up certificates for KM client
    root_dir = r"D:\New folder (8)\qumail-secure-email\qkd_kme_server-master\certs"
    
    # Alice's certificates (KME 1)
    km1_client_cert_path = os.path.join(root_dir, "kme-1-local-zone", "client_1_cert.pem")
    km1_client_key_path = os.path.join(root_dir, "kme-1-local-zone", "client_1.key")
    km1_ca_cert_path = os.path.join(root_dir, "kme-1-local-zone", "ca.crt")
    
    # Create SSL context
    ssl_context = await setup_ssl_context(km1_client_cert_path, km1_client_key_path, km1_ca_cert_path)
    
    # Try with much longer timeout (120 seconds)
    try:
        print("Testing key request with 120 second timeout...")
        async with httpx.AsyncClient(
            verify=ssl_context, 
            base_url="https://localhost:13000",
            timeout=httpx.Timeout(120.0)
        ) as client:
            # Check key status first
            response = await client.get("/api/v1/keys/3/status")
            response.raise_for_status()
            status = response.json()
            print(f"Key status: {json.dumps(status, indent=2)}")
            
            # Request encryption key with longer timeout
            print("Requesting encryption key (this may take some time)...")
            payload = {"number": 1}
            response = await client.post("/api/v1/keys/3/enc_keys", json=payload)
            response.raise_for_status()
            
            keys_data = response.json()
            print(f"Key request response: {json.dumps(keys_data, indent=2)}")
            
            return True
    except Exception as e:
        print(f"Key request failed with 120s timeout: {e}")
        return False

async def test_with_different_endpoints():
    """Test different API endpoints to determine which ones work"""
    print("\n=== Testing different API endpoints ===")
    
    # Set up certificates for KM client
    root_dir = r"D:\New folder (8)\qumail-secure-email\qkd_kme_server-master\certs"
    
    # Alice's certificates (KME 1)
    km1_client_cert_path = os.path.join(root_dir, "kme-1-local-zone", "client_1_cert.pem")
    km1_client_key_path = os.path.join(root_dir, "kme-1-local-zone", "client_1.key")
    km1_ca_cert_path = os.path.join(root_dir, "kme-1-local-zone", "ca.crt")
    
    # Create SSL context
    ssl_context = await setup_ssl_context(km1_client_cert_path, km1_client_key_path, km1_ca_cert_path)
    
    # List of endpoints to test
    endpoints = [
        "/api/v1/sae/info/me",
        "/api/v1/keys/3/status",
        "/api/v1/keys/entropy/total",
        # We'll skip the problematic ones: "/api/v1/keys/3/enc_keys"
    ]
    
    results = {}
    
    try:
        async with httpx.AsyncClient(
            verify=ssl_context, 
            base_url="https://localhost:13000",
            timeout=30.0
        ) as client:
            for endpoint in endpoints:
                try:
                    print(f"Testing endpoint: {endpoint}")
                    response = await client.get(endpoint)
                    response.raise_for_status()
                    results[endpoint] = {
                        "status": "SUCCESS",
                        "status_code": response.status_code,
                        "response": response.json()
                    }
                    print(f"  Response: {json.dumps(response.json(), indent=2)}")
                except Exception as e:
                    results[endpoint] = {
                        "status": "FAILED",
                        "error": str(e)
                    }
                    print(f"  Error: {e}")
        
        return results
    except Exception as e:
        print(f"Error testing endpoints: {e}")
        return {"error": str(e)}

async def test_mock_key_with_real_encryption():
    """Test encryption with mock keys but real KM client connection"""
    print("\n=== Testing encryption with mock quantum key ===")
    
    try:
        # Import encryption function
        from app.services.encryption.level1_otp import encrypt_otp, decrypt_otp
        
        content = "This is a test message encrypted with mock quantum key but real KM connection!"
        user_email = "test@example.com"
        
        # Generate mock quantum key
        mock_key = os.urandom(32)  # 256-bit key
        
        # Set up certificates for KM client
        root_dir = r"D:\New folder (8)\qumail-secure-email\qkd_kme_server-master\certs"
        km1_client_cert_path = os.path.join(root_dir, "kme-1-local-zone", "client_1_cert.pem")
        km1_client_key_path = os.path.join(root_dir, "kme-1-local-zone", "client_1.key")
        km1_ca_cert_path = os.path.join(root_dir, "kme-1-local-zone", "ca.crt")
        
        # Create SSL context
        ssl_context = await setup_ssl_context(km1_client_cert_path, km1_client_key_path, km1_ca_cert_path)
        
        # Verify KM connection first
        async with httpx.AsyncClient(verify=ssl_context, base_url="https://localhost:13000") as client:
            response = await client.get("/api/v1/sae/info/me")
            response.raise_for_status()
            print(f"KM connection verified: {response.text}")
        
        # Now encrypt with mock key
        print("Encrypting with OTP using mock quantum key...")
        encrypted_result = await encrypt_otp(content, user_email, qkd_key=mock_key)
        
        print(f"Encrypted successfully with algorithm: {encrypted_result['algorithm']}")
        print(f"Encrypted content length: {len(encrypted_result['encrypted_content'])}")
        
        print("Decrypting with OTP...")
        # Copy signature to metadata for proper decryption
        metadata = encrypted_result['metadata']
        metadata['signature'] = encrypted_result['signature']
        metadata['public_key'] = encrypted_result.get('metadata', {}).get('public_key')
        
        decrypted_result = await decrypt_otp(
            encrypted_result['encrypted_content'],
            user_email,
            metadata,
            qkd_key=mock_key  # Use same key for test
        )
        
        success = decrypted_result['decrypted_content'] == content
        print(f"Decryption successful: {success}")
        print(f"Decrypted content: {decrypted_result['decrypted_content']}")
        
        return success
    except Exception as e:
        print(f"Mock key encryption test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run tests with increased timeout and alternative approaches"""
    print("="*80)
    print("  QUMAIL SECURE EMAIL - KM SERVER CONNECTION TROUBLESHOOTING")
    print("  (Testing with increased timeouts and alternative approaches)")
    print("="*80)
    
    results = {}
    
    # Test different API endpoints
    print("\n--- Testing KM Server API Endpoints ---")
    api_results = await test_with_different_endpoints()
    
    # Test key request with increased timeout
    print("\n--- Testing Key Request with Increased Timeout ---")
    results["Key Request with 120s Timeout"] = await test_key_request_with_timeout()
    
    # Test mock key with real encryption
    print("\n--- Testing Encryption with Mock Keys ---")
    results["Encryption with Mock Keys"] = await test_mock_key_with_real_encryption()
    
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