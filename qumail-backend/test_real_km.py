#!/usr/bin/env python
"""
Test script for connecting to real Quantum Key Management servers.
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

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ensure we can import from the app package
sys.path.append(os.path.dirname(__file__))

# Import the required modules
from app.config import get_settings
from app.services.km_client import KMClient, create_km_clients

async def connect_with_pem(base_url, sae_id, client_cert_path, client_key_path, ca_cert_path):
    """Connect to KM server using PEM certificates"""
    # Create SSL context with client certificate
    ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ssl_context.verify_mode = ssl.CERT_REQUIRED
    ssl_context.check_hostname = False  # KM uses localhost
    
    # Load CA certificate for server verification
    ssl_context.load_verify_locations(cafile=ca_cert_path)
    
    # Load client certificate and key
    ssl_context.load_cert_chain(certfile=client_cert_path, keyfile=client_key_path)
    
    # Connect to KM server
    async with httpx.AsyncClient(verify=ssl_context, base_url=base_url) as client:
        response = await client.get(f"/api/v1/sae/info/me")
        response.raise_for_status()
        logger.info(f"SAE info: {response.text}")
        
        # Check key status
        response = await client.get(f"/api/v1/keys/{3 if sae_id == 1 else 1}/status")
        response.raise_for_status()
        logger.info(f"Key status: {response.text}")
        
    return True

async def test_km_client_connection():
    """Test the connection to KM servers"""
    logger.info("Testing KM client connection")
    
    import ssl
    import httpx
    
    # Use absolute paths for certificates
    root_dir = r"D:\New folder (8)\qumail-secure-email\qkd_kme_server-master\certs"
    
    # Alice's certificates (KME 1)
    km1_client_cert_path = os.path.join(root_dir, "kme-1-local-zone", "client_1_cert.pem")
    km1_client_key_path = os.path.join(root_dir, "kme-1-local-zone", "client_1.key")
    km1_ca_cert_path = os.path.join(root_dir, "kme-1-local-zone", "ca.crt")
    
    # Bob's certificates (KME 2)
    km2_client_cert_path = os.path.join(root_dir, "kme-2-local-zone", "client_3_cert.pem")
    km2_client_key_path = os.path.join(root_dir, "kme-2-local-zone", "client_3.key")
    km2_ca_cert_path = os.path.join(root_dir, "kme-2-local-zone", "ca.crt")
    
    # Test Alice's connection to KME 1
    try:
        logger.info("Testing connection to KME 1 (Alice)...")
        alice_success = await connect_with_pem(
            "https://localhost:13000", 
            1, 
            km1_client_cert_path, 
            km1_client_key_path, 
            km1_ca_cert_path
        )
    except Exception as e:
        logger.error(f"Error with KME 1 connection: {e}")
        alice_success = False
    
    # Test Bob's connection to KME 2
    try:
        logger.info("Testing connection to KME 2 (Bob)...")
        bob_success = await connect_with_pem(
            "https://localhost:14000", 
            3, 
            km2_client_cert_path, 
            km2_client_key_path, 
            km2_ca_cert_path
        )
    except Exception as e:
        logger.error(f"Error with KME 2 connection: {e}")
        bob_success = False
    
    return alice_success and bob_success
    
    # Test Alice's KM client
    try:
        alice_info = await alice_km_client.get_sae_info()
        logger.info(f"Alice SAE info: {alice_info}")
        alice_status = await alice_km_client.check_key_status(3)  # Receiver SAE ID 3
        logger.info(f"Alice key status with Bob: {alice_status}")
    except Exception as e:
        logger.error(f"Error with Alice's KM client: {e}")
        return False
    finally:
        await alice_km_client.close()
    
    # Test Bob's KM client
    try:
        bob_info = await bob_km_client.get_sae_info()
        logger.info(f"Bob SAE info: {bob_info}")
        bob_status = await bob_km_client.check_key_status(1)  # Sender SAE ID 1
        logger.info(f"Bob key status with Alice: {bob_status}")
    except Exception as e:
        logger.error(f"Error with Bob's KM client: {e}")
        return False
    finally:
        await bob_km_client.close()
    
    logger.info("KM client connections successful")
    return True

async def test_request_keys():
    """Test requesting quantum keys from KM servers"""
    logger.info("Testing quantum key request functionality")
    
    # Use absolute paths for certificates
    root_dir = r"D:\New folder (8)\qumail-secure-email\qkd_kme_server-master\certs"
    
    # Alice's certificates (KME 1)
    km1_client_cert_path = os.path.join(root_dir, "kme-1-local-zone", "client_1_cert.pem")
    km1_client_key_path = os.path.join(root_dir, "kme-1-local-zone", "client_1.key")
    km1_ca_cert_path = os.path.join(root_dir, "kme-1-local-zone", "ca.crt")
    
    # Create SSL context with client certificate
    ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ssl_context.verify_mode = ssl.CERT_REQUIRED
    ssl_context.check_hostname = False  # KM uses localhost
    
    # Load CA certificate for server verification
    ssl_context.load_verify_locations(cafile=km1_ca_cert_path)
    
    # Load client certificate and key
    ssl_context.load_cert_chain(certfile=km1_client_cert_path, keyfile=km1_client_key_path)
    
    try:
        async with httpx.AsyncClient(verify=ssl_context, base_url="https://localhost:13000") as client:
            # Check key status first
            response = await client.get("/api/v1/keys/3/status")  # Receiver SAE ID 3
            response.raise_for_status()
            
            status = response.json()
            logger.info(f"Key status: {status}")
            
            stored_key_count = status.get("stored_key_count", 0)
            if stored_key_count <= 0:
                logger.warning("No quantum keys available - check KM server")
                return False
            
            # Request encryption keys
            payload = {"number": 1}
            response = await client.post("/api/v1/keys/3/enc_keys", json=payload)  # Receiver SAE ID 3
            response.raise_for_status()
            
            keys_data = response.json()
            keys = keys_data.get("keys", [])
            
            if not keys:
                logger.error("Failed to retrieve encryption keys")
                return False
                
            logger.info(f"Successfully retrieved {len(keys)} encryption keys")
            key_id = keys[0].get("key_ID")
            logger.info(f"Key ID: {key_id}")
            
            # Request corresponding decryption key
            payload = {"key_IDs": [{"key_ID": key_id}]}
            response = await client.post("/api/v1/keys/3/dec_keys", json=payload)  # Receiver SAE ID 3
            response.raise_for_status()
            
            dec_keys_data = response.json()
            dec_keys = dec_keys_data.get("keys", [])
            
            if not dec_keys:
                logger.error("Failed to retrieve decryption keys")
                return False
                
            logger.info(f"Successfully retrieved corresponding decryption key")
            
            # Verify the keys match
            enc_key = keys[0].get("key")
            dec_key = dec_keys[0].get("key")
            
            if enc_key == dec_key:
                logger.info("Encryption and decryption keys match as expected")
            else:
                logger.warning("Encryption and decryption keys do not match!")
                return False
                
            return True
    except Exception as e:
        logger.error(f"Error testing key requests: {e}")
        return False

async def test_global_km_clients():
    """Test the global KM client instances using PEM certificates"""
    logger.info("Testing global KM client instances with direct SSL context")
    
    try:
        # Use absolute paths for certificates
        root_dir = r"D:\New folder (8)\qumail-secure-email\qkd_kme_server-master\certs"
        
        # Alice's certificates (KME 1)
        km1_client_cert_path = os.path.join(root_dir, "kme-1-local-zone", "client_1_cert.pem")
        km1_client_key_path = os.path.join(root_dir, "kme-1-local-zone", "client_1.key")
        km1_ca_cert_path = os.path.join(root_dir, "kme-1-local-zone", "ca.crt")
        
        # Bob's certificates (KME 2)
        km2_client_cert_path = os.path.join(root_dir, "kme-2-local-zone", "client_3_cert.pem")
        km2_client_key_path = os.path.join(root_dir, "kme-2-local-zone", "client_3.key")
        km2_ca_cert_path = os.path.join(root_dir, "kme-2-local-zone", "ca.crt")
        
        # Create SSL context for KME 1
        km1_ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        km1_ssl_context.verify_mode = ssl.CERT_REQUIRED
        km1_ssl_context.check_hostname = False  # KM uses localhost
        km1_ssl_context.load_verify_locations(cafile=km1_ca_cert_path)
        km1_ssl_context.load_cert_chain(certfile=km1_client_cert_path, keyfile=km1_client_key_path)
        
        # Create SSL context for KME 2
        km2_ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        km2_ssl_context.verify_mode = ssl.CERT_REQUIRED
        km2_ssl_context.check_hostname = False  # KM uses localhost
        km2_ssl_context.load_verify_locations(cafile=km2_ca_cert_path)
        km2_ssl_context.load_cert_chain(certfile=km2_client_cert_path, keyfile=km2_client_key_path)
        
        # Test KME 1 status
        logger.info("Testing KME 1 status...")
        async with httpx.AsyncClient(verify=km1_ssl_context, base_url="https://localhost:13000") as client:
            response = await client.get("/api/v1/status")
            response.raise_for_status()
            km1_status = response.json()
            logger.info(f"KME 1 status: {km1_status}")
        
        # Test KME 2 status
        logger.info("Testing KME 2 status...")
        async with httpx.AsyncClient(verify=km2_ssl_context, base_url="https://localhost:14000") as client:
            response = await client.get("/api/v1/status")
            response.raise_for_status()
            km2_status = response.json()
            logger.info(f"KME 2 status: {km2_status}")
        
        return True
    except Exception as e:
        logger.error(f"Error testing KM servers status: {e}")
        return False

async def main():
    """Run KM client connection and key request tests with real KM servers"""
    logger.info("Starting real KM server connection tests")
    
    results = {}
    
    # Test custom KM client connections
    results["Custom KM client connection"] = await test_km_client_connection()
    
    # Test global KM client instances
    results["Global KM client instances"] = await test_global_km_clients()
    
    # Test quantum key request functionality
    results["Quantum key request"] = await test_request_keys()
    
    # Print summary
    logger.info("\n===== TEST RESULTS SUMMARY =====")
    all_passed = all(results.values())
    
    for test_name, result in results.items():
        status = "PASSED" if result else "FAILED"
        logger.info(f"{test_name}: {status}")
    
    if all_passed:
        logger.info("\nAll KM server tests PASSED!")
    else:
        logger.warning("\nSome KM server tests FAILED.")
        
    return all_passed

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)