#!/usr/bin/env python3
"""
Direct POST Key Generation Test

Test making direct POST requests to generate keys for SAE pairs.
"""

import asyncio
import httpx
import ssl
import json

async def generate_keys_direct_post():
    """Make direct POST requests to generate keys"""
    
    print("🔑 DIRECT POST KEY GENERATION TEST")
    print("=" * 50)
    
    # SSL context for SAE-1
    cert_base = r"D:\New folder (8)\qumail-secure-email\next-door-key-simulator\certs"
    ssl_context1 = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ssl_context1.load_verify_locations(f"{cert_base}\\ca.crt.pem")
    ssl_context1.load_cert_chain(f"{cert_base}\\sae-1.crt.pem", f"{cert_base}\\sae-1.key.pem")
    ssl_context1.check_hostname = False
    
    # SSL context for SAE-2
    ssl_context2 = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ssl_context2.load_verify_locations(f"{cert_base}\\ca.crt.pem")
    ssl_context2.load_cert_chain(f"{cert_base}\\sae-2.crt.pem", f"{cert_base}\\sae-2.key.pem")
    ssl_context2.check_hostname = False
    
    print("\n1️⃣ Requesting keys from KME-1 via POST...")
    try:
        async with httpx.AsyncClient(verify=ssl_context1, timeout=30.0) as client1:
            response = await client1.post(
                "https://127.0.0.1:8010/api/v1/keys/c565d5aa-8670-4446-8471-b0e53e315d2a/enc_keys",
                json={
                    "number": 1,
                    "size": 32
                }
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Generated {len(data.get('keys', []))} keys")
                if data.get('keys'):
                    print(f"   First Key: {data['keys'][0]['key'][:32]}...")
            else:
                print(f"   Error: {response.text}")
                
    except Exception as e:
        print(f"   Exception: {e}")
    
    print("\n2️⃣ Requesting keys from KME-2 via POST...")
    try:
        async with httpx.AsyncClient(verify=ssl_context2, timeout=30.0) as client2:
            response = await client2.post(
                "https://127.0.0.1:8020/api/v1/keys/25840139-0dd4-49ae-ba1e-b86731601803/enc_keys",
                json={
                    "number": 1,
                    "size": 32
                }
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Generated {len(data.get('keys', []))} keys")
                if data.get('keys'):
                    print(f"   First Key: {data['keys'][0]['key'][:32]}...")
            else:
                print(f"   Error: {response.text}")
                
    except Exception as e:
        print(f"   Exception: {e}")
    
    print("\n3️⃣ Checking status after key generation...")
    
    # Check KME-1 status
    try:
        async with httpx.AsyncClient(verify=ssl_context1, timeout=30.0) as client1:
            response = await client1.get("https://127.0.0.1:8010/api/v1/keys/c565d5aa-8670-4446-8471-b0e53e315d2a/status")
            if response.status_code == 200:
                data = response.json()
                print(f"   KME-1 -> SAE-2: {data['stored_key_count']} keys available")
            else:
                print(f"   KME-1 Status Error: {response.text}")
    except Exception as e:
        print(f"   KME-1 Status Exception: {e}")
    
    # Check KME-2 status  
    try:
        async with httpx.AsyncClient(verify=ssl_context2, timeout=30.0) as client2:
            response = await client2.get("https://127.0.0.1:8020/api/v1/keys/25840139-0dd4-49ae-ba1e-b86731601803/status")
            if response.status_code == 200:
                data = response.json()
                print(f"   KME-2 -> SAE-1: {data['stored_key_count']} keys available")
            else:
                print(f"   KME-2 Status Error: {response.text}")
    except Exception as e:
        print(f"   KME-2 Status Exception: {e}")

if __name__ == "__main__":
    asyncio.run(generate_keys_direct_post())