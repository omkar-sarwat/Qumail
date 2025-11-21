#!/usr/bin/env python
"""
Test script for checking the correct password for PKCS12 PFX certificates
"""

import os
import sys
import logging
from cryptography.hazmat.primitives.serialization import pkcs12

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def try_load_certificate(pfx_path, password=None):
    """Try to load a PKCS12 certificate with given password"""
    try:
        with open(pfx_path, 'rb') as f:
            pfx_data = f.read()
        
        if password:
            password = password.encode()
        
        # Try to load the certificate
        private_key, certificate, additional_certificates = pkcs12.load_key_and_certificates(
            pfx_data, password
        )
        
        logger.info(f"SUCCESS! Certificate loaded with password: {password}")
        return True
    except Exception as e:
        logger.error(f"Failed to load certificate: {e}")
        return False

def main():
    # Paths to the client certificates
    client1_pfx = r"D:\New folder (8)\qumail-secure-email\qkd_kme_server-master\certs\kme-1-local-zone\client_1.pfx"
    client3_pfx = r"D:\New folder (8)\qumail-secure-email\qkd_kme_server-master\certs\kme-2-local-zone\client_3.pfx"
    
    # Try with empty password
    logger.info("\nTrying with empty password...")
    client1_success = try_load_certificate(client1_pfx, "")
    client3_success = try_load_certificate(client3_pfx, "")
    
    # Try with 'password'
    logger.info("\nTrying with 'password'...")
    if not client1_success:
        client1_success = try_load_certificate(client1_pfx, "password")
    if not client3_success:
        client3_success = try_load_certificate(client3_pfx, "password")
    
    # Try with None
    logger.info("\nTrying with None...")
    if not client1_success:
        client1_success = try_load_certificate(client1_pfx, None)
    if not client3_success:
        client3_success = try_load_certificate(client3_pfx, None)
    
    if client1_success and client3_success:
        logger.info("\nAll certificates loaded successfully!")
    else:
        logger.error("\nFailed to load one or more certificates.")

if __name__ == "__main__":
    main()