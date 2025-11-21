#!/usr/bin/env python
"""
Test script for connecting to real Quantum Key Management servers using PEM certificates.
"""

import os
import sys
import logging
import asyncio
import ssl
import tempfile
import shutil
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ensure we can import from the app package
sys.path.append(os.path.dirname(__file__))

import httpx

async def test_km_connection_with_pem():
    """Test connecting to KM server using PEM certificate format"""
    logger.info("Testing KM connection with PEM certificates")
    
    # Certificate paths
    root_dir = r"D:\New folder (8)\qumail-secure-email\qkd_kme_server-master\certs"
    client_cert_path = os.path.join(root_dir, "kme-1-local-zone", "client_1_cert.pem")
    client_key_path = os.path.join(root_dir, "kme-1-local-zone", "client_1.key")
    ca_cert_path = os.path.join(root_dir, "kme-1-local-zone", "ca.crt")
    
    # Create SSL context with client certificate
    ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ssl_context.verify_mode = ssl.CERT_REQUIRED
    ssl_context.check_hostname = False  # KM uses localhost
    
    # Load CA certificate for server verification
    ssl_context.load_verify_locations(cafile=ca_cert_path)
    
    # Load client certificate and key
    ssl_context.load_cert_chain(certfile=client_cert_path, keyfile=client_key_path)
    
    # Test connection to KM server
    try:
        async with httpx.AsyncClient(verify=ssl_context) as client:
            response = await client.get("https://localhost:13000/api/v1/sae/info/me", timeout=10)
            response.raise_for_status()
            logger.info(f"Successfully connected to KM server: {response.status_code}")
            logger.info(f"Response: {response.text}")
            return True
    except Exception as e:
        logger.error(f"Failed to connect to KM server: {e}")
        return False

async def main():
    """Run tests for KM server connection"""
    logger.info("Testing KM server connection with PEM certificates")
    
    result = await test_km_connection_with_pem()
    
    if result:
        logger.info("Test PASSED - Successfully connected to KM server")
    else:
        logger.error("Test FAILED - Could not connect to KM server")
    
    return result

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)