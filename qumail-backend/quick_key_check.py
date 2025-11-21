#!/usr/bin/env python3
"""
Quick key availability check after KME restart
"""
import asyncio
import sys
from app.services.optimized_km_client import OptimizedKMClient

async def quick_key_check():
    """Quick check if keys are now available"""
    print("⚡ QUICK KEY AVAILABILITY CHECK")
    print("=" * 40)
    
    # KME-1 Configuration (port 8010)
    kme1_client = OptimizedKMClient(
        base_url="https://127.0.0.1:8010",
        sae_id="25840139-0dd4-49ae-ba1e-b86731601803",
        ca_cert_path="../next-door-key-simulator/certs/ca.crt.pem",
        client_cert_path="../next-door-key-simulator/certs/sae-1.crt.pem", 
        client_key_path="../next-door-key-simulator/certs/sae-1.key.pem"
    )
    
    try:
        print("🔍 Checking KME-1 key availability...")
        status1 = await kme1_client.check_key_status("c565d5aa-8670-4446-8471-b0e53e315d2a")
        available1 = status1.get('stored_key_count', 0)
        print(f"   KME-1: {available1} keys available")
        
        if available1 > 0:
            print("   🎯 Attempting key generation from KME-1...")
            keys1 = await kme1_client.request_enc_keys("c565d5aa-8670-4446-8471-b0e53e315d2a", 256, 1)
            if keys1 and len(keys1) > 0:
                print(f"   ✅ SUCCESS! Got key from KME-1: {keys1[0]['key_ID'][:16]}...")
            else:
                print("   ❌ Failed to get key from KME-1")
        
    except Exception as e:
        print(f"   ❌ KME-1 error: {e}")
    
    await kme1_client.close()
    print("\n✅ Quick check complete!")

if __name__ == "__main__":
    asyncio.run(quick_key_check())