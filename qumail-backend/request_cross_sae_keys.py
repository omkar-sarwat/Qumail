#!/usr/bin/env python3
"""
Request Cross-SAE Keys

Request keys for cross-SAE communication directly using the proper API.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.optimized_km_client import OptimizedKMClient

async def request_cross_sae_keys():
    """Request keys for cross-SAE communication"""
    
    print("🔑 REQUESTING CROSS-SAE KEYS")
    print("=" * 50)
    
    # Initialize KME clients with SSL certificates
    cert_base = r"D:\New folder (8)\qumail-secure-email\next-door-key-simulator\certs"
    
    # KME1 client (for SAE 25840139-0dd4-49ae-ba1e-b86731601803)
    km1_client = OptimizedKMClient(
        base_url="https://127.0.0.1:8010",
        sae_id="25840139-0dd4-49ae-ba1e-b86731601803",
        client_cert_path=f"{cert_base}\\sae-1.crt.pem",
        client_key_path=f"{cert_base}\\sae-1.key.pem",
        ca_cert_path=f"{cert_base}\\ca.crt.pem"
    )
    
    # KME2 client (for SAE c565d5aa-8670-4446-8471-b0e53e315d2a)
    km2_client = OptimizedKMClient(
        base_url="https://127.0.0.1:8020", 
        sae_id="c565d5aa-8670-4446-8471-b0e53e315d2a",
        client_cert_path=f"{cert_base}\\sae-2.crt.pem",
        client_key_path=f"{cert_base}\\sae-2.key.pem",
        ca_cert_path=f"{cert_base}\\ca.crt.pem"
    )
    
    print("\n1️⃣ Requesting keys from KME-1 for cross-SAE communication...")
    try:
        # Request from KME-1 for keys to communicate with the other SAE
        keys1 = await km1_client.request_enc_keys(
            slave_sae_id="c565d5aa-8670-4446-8471-b0e53e315d2a",  # Request keys for other SAE
            size=256,  # 32 bytes * 8 bits
            number=1   # Request just 1 key first
        )
        print(f"   ✅ KME-1 Generated Keys: {len(keys1) if keys1 else 0}")
        if keys1:
            print(f"   First Key: {keys1[0]['key'][:32]}...")
        
    except Exception as e:
        print(f"   ❌ KME-1 Error: {e}")
    
    print("\n2️⃣ Requesting keys from KME-2 for cross-SAE communication...")
    try:
        # Request from KME-2 for keys to communicate with the other SAE
        keys2 = await km2_client.request_enc_keys(
            slave_sae_id="25840139-0dd4-49ae-ba1e-b86731601803",  # Request keys for other SAE
            size=256,  # 32 bytes * 8 bits
            number=1   # Request just 1 key first
        )
        print(f"   ✅ KME-2 Generated Keys: {len(keys2) if keys2 else 0}")
        if keys2:
            print(f"   First Key: {keys2[0]['key'][:32]}...")
        
    except Exception as e:
        print(f"   ❌ KME-2 Error: {e}")
    
    print("\n3️⃣ Checking status after key generation...")
    
    # Check KME-1 status for cross-SAE communication
    try:
        status1 = await km1_client.check_key_status("c565d5aa-8670-4446-8471-b0e53e315d2a")
        print(f"   KME-1 -> SAE-2 Status: {status1['stored_key_count']} keys available")
    except Exception as e:
        print(f"   KME-1 Status Error: {e}")
    
    # Check KME-2 status for cross-SAE communication  
    try:
        status2 = await km2_client.check_key_status("25840139-0dd4-49ae-ba1e-b86731601803")
        print(f"   KME-2 -> SAE-1 Status: {status2['stored_key_count']} keys available")
    except Exception as e:
        print(f"   KME-2 Status Error: {e}")

if __name__ == "__main__":
    asyncio.run(request_cross_sae_keys())