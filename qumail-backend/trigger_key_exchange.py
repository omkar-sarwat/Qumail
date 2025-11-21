#!/usr/bin/env python3
"""
Trigger KME Key Exchange

Force key exchange between the two KME servers to populate key pools.
"""

import asyncio
import httpx
import ssl
import sys
import os

async def trigger_key_exchange():
    """Trigger key exchange between KME servers"""
    
    print("🔄 TRIGGERING KME KEY EXCHANGE")
    print("=" * 50)
    
    # SSL context for mutual TLS authentication
    cert_base = r"D:\New folder (8)\qumail-secure-email\next-door-key-simulator\certs"
    ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ssl_context.load_verify_locations(f"{cert_base}\\ca.crt.pem")
    ssl_context.load_cert_chain(f"{cert_base}\\sae-1.crt.pem", f"{cert_base}\\sae-1.key.pem")
    ssl_context.check_hostname = False  # Disable hostname verification for localhost
    
    # Create HTTP client with SSL
    async with httpx.AsyncClient(verify=ssl_context, timeout=30.0) as client:
        
        print("\n1️⃣ Triggering key exchange from KME-1...")
        try:
            # Try to trigger key exchange POST request
            response = await client.post(
                "https://127.0.0.1:8010/api/v1/kme/keys/exchange",
                json={
                    "master_SAE_ID": "25840139-0dd4-49ae-ba1e-b86731601803",
                    "slave_SAE_ID": "c565d5aa-8670-4446-8471-b0e53e315d2a",
                    "target_KME_ID": "ffb23f4d-5d5b-47e5-a8c5-fe9e47d646cd",
                    "number": 10,
                    "size": 32
                }
            )
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text}")
            
        except Exception as e:
            print(f"   Error: {e}")
        
        print("\n2️⃣ Triggering key exchange from KME-2...")
        try:
            # Switch to SAE-2 certificate for KME-2
            ssl_context2 = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            ssl_context2.load_verify_locations(f"{cert_base}\\ca.crt.pem")
            ssl_context2.load_cert_chain(f"{cert_base}\\sae-2.crt.pem", f"{cert_base}\\sae-2.key.pem")
            ssl_context2.check_hostname = False  # Disable hostname verification for localhost
            
            async with httpx.AsyncClient(verify=ssl_context2, timeout=30.0) as client2:
                response = await client2.post(
                    "https://127.0.0.1:8020/api/v1/kme/keys/exchange",
                    json={
                        "master_SAE_ID": "c565d5aa-8670-4446-8471-b0e53e315d2a",
                        "slave_SAE_ID": "25840139-0dd4-49ae-ba1e-b86731601803",
                        "target_KME_ID": "9b7703f1-9b6d-403d-b850-18a1b6fd6d8f",
                        "number": 10,
                        "size": 32
                    }
                )
                print(f"   Status: {response.status_code}")
                print(f"   Response: {response.text}")
            
        except Exception as e:
            print(f"   Error: {e}")
        
        print("\n3️⃣ Checking key status after exchange...")
        
        # Check KME-1 status
        try:
            response = await client.get("https://127.0.0.1:8010/api/v1/keys/25840139-0dd4-49ae-ba1e-b86731601803/status")
            print(f"   KME-1 Status: {response.json()}")
        except Exception as e:
            print(f"   KME-1 Status Error: {e}")
        
        # Check KME-2 status  
        try:
            ssl_context2 = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            ssl_context2.load_verify_locations(f"{cert_base}\\ca.crt.pem")
            ssl_context2.load_cert_chain(f"{cert_base}\\sae-2.crt.pem", f"{cert_base}\\sae-2.key.pem")
            ssl_context2.check_hostname = False  # Disable hostname verification for localhost
            
            async with httpx.AsyncClient(verify=ssl_context2, timeout=30.0) as client2:
                response = await client2.get("https://127.0.0.1:8020/api/v1/keys/c565d5aa-8670-4446-8471-b0e53e315d2a/status")
                print(f"   KME-2 Status: {response.json()}")
        except Exception as e:
            print(f"   KME-2 Status Error: {e}")

if __name__ == "__main__":
    asyncio.run(trigger_key_exchange())