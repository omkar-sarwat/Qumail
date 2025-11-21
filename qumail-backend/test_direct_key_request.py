#!/usr/bin/env python3
"""
Direct KME Key Request Test

Test direct key requests from KME servers to see if keys are being properly exchanged.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.optimized_km_client import OptimizedKMClient

async def test_direct_key_requests():
    """Test direct key requests from both KME servers"""
    
    print("🔑 DIRECT KME KEY REQUEST TEST")
    print("=" * 50)
    
    # Initialize KME clients with SSL certificates
    cert_base = r"D:\New folder (8)\qumail-secure-email\next-door-key-simulator\certs"
    
    km1_client = OptimizedKMClient(
        base_url="https://127.0.0.1:8010",
        sae_id="25840139-0dd4-49ae-ba1e-b86731601803",
        client_cert_path=f"{cert_base}\\sae-1.crt.pem",
        client_key_path=f"{cert_base}\\sae-1.key.pem",
        ca_cert_path=f"{cert_base}\\ca.crt.pem"
    )
    
    km2_client = OptimizedKMClient(
        base_url="https://127.0.0.1:8020", 
        sae_id="c565d5aa-8670-4446-8471-b0e53e315d2a",
        client_cert_path=f"{cert_base}\\sae-2.crt.pem",
        client_key_path=f"{cert_base}\\sae-2.key.pem",
        ca_cert_path=f"{cert_base}\\ca.crt.pem"
    )
    
    print("\n1️⃣ Testing KME-1 direct key request...")
    try:
        # Check status first
        status1 = await km1_client.check_key_status("25840139-0dd4-49ae-ba1e-b86731601803")
        print(f"   KME-1 Status: {status1}")
        
        # Try to request keys
        keys1 = await km1_client.request_enc_keys(
            slave_sae_id="25840139-0dd4-49ae-ba1e-b86731601803",
            size=256,  # 32 bytes * 8 bits
            number=1
        )
        print(f"   KME-1 Keys: {keys1}")
        
    except Exception as e:
        print(f"   KME-1 Error: {e}")
    
    print("\n2️⃣ Testing KME-2 direct key request...")
    try:
        # Check status first
        status2 = await km2_client.check_key_status("c565d5aa-8670-4446-8471-b0e53e315d2a")
        print(f"   KME-2 Status: {status2}")
        
        # Try to request keys
        keys2 = await km2_client.request_enc_keys(
            slave_sae_id="c565d5aa-8670-4446-8471-b0e53e315d2a",
            size=256,  # 32 bytes * 8 bits
            number=1
        )
        print(f"   KME-2 Keys: {keys2}")
        
    except Exception as e:
        print(f"   KME-2 Error: {e}")
    
    print("\n3️⃣ Testing cross-KME key exchange...")
    try:
        # Try requesting from KME-1 for KME-2's SAE ID
        print("   Testing KME-1 -> KME-2 SAE cross-request...")
        cross_keys = await km1_client.request_enc_keys(
            slave_sae_id="c565d5aa-8670-4446-8471-b0e53e315d2a",
            size=256,
            number=1
        )
        print(f"   Cross Keys: {cross_keys}")
        
    except Exception as e:
        print(f"   Cross Request Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_direct_key_requests())