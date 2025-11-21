#!/usr/bin/env python3
"""
Debug KME API to understand the SAE relationship requirements
"""
import asyncio
import httpx
import ssl
import json
from pathlib import Path

async def test_kme_api():
    print("🔍 DEBUGGING KME API ENDPOINTS WITH PROPER SSL")
    print("=" * 50)
    
    base_certs = Path("../next-door-key-simulator/certs")
    
    # Setup proper SSL context with certificates
    ssl_context1 = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ssl_context1.minimum_version = ssl.TLSVersion.TLSv1_2
    ssl_context1.check_hostname = False
    ssl_context1.load_verify_locations(cafile=str(base_certs / "ca.crt.pem"))
    ssl_context1.load_cert_chain(
        certfile=str(base_certs / "sae-1.crt.pem"),
        keyfile=str(base_certs / "sae-1.key.pem")
    )
    
    ssl_context2 = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ssl_context2.minimum_version = ssl.TLSVersion.TLSv1_2
    ssl_context2.check_hostname = False
    ssl_context2.load_verify_locations(cafile=str(base_certs / "ca.crt.pem"))
    ssl_context2.load_cert_chain(
        certfile=str(base_certs / "sae-2.crt.pem"),
        keyfile=str(base_certs / "sae-2.key.pem")
    )
    
    try:
        # Test 1: Check KME internal status
        print("\n1️⃣ Testing KME internal status with SSL...")
        
        # KME-1 with proper SSL
        async with httpx.AsyncClient(verify=ssl_context1) as client1:
            response1 = await client1.get("https://127.0.0.1:8010/api/v1/kme/status")
            print(f"KME-1 Internal Status: {response1.status_code}")
            if response1.status_code == 200:
                print(f"   Data: {response1.json()}")
            
        # KME-2 with proper SSL
        async with httpx.AsyncClient(verify=ssl_context2) as client2:
            response2 = await client2.get("https://127.0.0.1:8020/api/v1/kme/status")
            print(f"KME-2 Internal Status: {response2.status_code}")
            if response2.status_code == 200:
                print(f"   Data: {response2.json()}")
        
        # Test 2: Check key pools
        print("\n2️⃣ Testing KME key pools...")
        async with httpx.AsyncClient(verify=ssl_context1) as client1:
            response1 = await client1.get("https://127.0.0.1:8010/api/v1/kme/key-pool")
            print(f"KME-1 Key Pool: {response1.status_code}")
            if response1.status_code == 200:
                data1 = response1.json()
                print(f"   Keys available: {len(data1.get('keys', []))}")
                print(f"   Pool data: {data1}")
            
        async with httpx.AsyncClient(verify=ssl_context2) as client2:
            response2 = await client2.get("https://127.0.0.1:8020/api/v1/kme/key-pool")  
            print(f"KME-2 Key Pool: {response2.status_code}")
            if response2.status_code == 200:
                data2 = response2.json()
                print(f"   Keys available: {len(data2.get('keys', []))}")
                print(f"   Pool data: {data2}")
    
        # Test 3: Check SAE key status (what our system is checking)
        print("\n3️⃣ Testing SAE key availability...")
        async with httpx.AsyncClient(verify=ssl_context1) as client1:
            response1 = await client1.get("https://127.0.0.1:8010/api/v1/keys/c565d5aa-8670-4446-8471-b0e53e315d2a/status")
            print(f"KME-1 -> SAE-2 Status: {response1.status_code}")
            if response1.status_code == 200:
                print(f"   Available keys: {response1.json()}")
            elif response1.status_code == 404:
                print("   ❌ SAE-2 not found on KME-1")
            else:
                print(f"   Error: {response1.status_code} - {response1.text}")
                
        async with httpx.AsyncClient(verify=ssl_context2) as client2:
            response2 = await client2.get("https://127.0.0.1:8020/api/v1/keys/25840139-0dd4-49ae-ba1e-b86731601803/status")
            print(f"KME-2 -> SAE-1 Status: {response2.status_code}")
            if response2.status_code == 200:
                print(f"   Available keys: {response2.json()}")
            elif response2.status_code == 404:
                print("   ❌ SAE-1 not found on KME-2")
            else:
                print(f"   Error: {response2.status_code} - {response2.text}")

        # Test 4: Try to request keys directly 
        print("\n4️⃣ Testing direct key requests...")
        async with httpx.AsyncClient(verify=ssl_context1) as client1:
            try:
                # Try requesting keys from KME-1 for SAE-2
                payload = {"number": 1}
                response = await client1.post(
                    "https://127.0.0.1:8010/api/v1/keys/c565d5aa-8670-4446-8471-b0e53e315d2a/enc_keys",
                    json=payload
                )
                print(f"KME-1 Key Request: {response.status_code}")
                if response.status_code == 200:
                    print(f"   Got keys: {response.json()}")
                else:
                    print(f"   Failed: {response.text}")
            except Exception as e:
                print(f"   Error requesting keys: {e}")
                
        async with httpx.AsyncClient(verify=ssl_context2) as client2:
            try:
                # Try requesting keys from KME-2 for SAE-1
                payload = {"number": 1}
                response = await client2.post(
                    "https://127.0.0.1:8020/api/v1/keys/25840139-0dd4-49ae-ba1e-b86731601803/enc_keys",
                    json=payload
                )
                print(f"KME-2 Key Request: {response.status_code}")
                if response.status_code == 200:
                    print(f"   Got keys: {response.json()}")
                else:
                    print(f"   Failed: {response.text}")
            except Exception as e:
                print(f"   Error requesting keys: {e}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_kme_api())