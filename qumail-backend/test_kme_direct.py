#!/usr/bin/env python3
"""
Direct test of KME servers to understand key availability
"""
import asyncio
import sys
import time
from app.services.optimized_km_client import OptimizedKMClient

async def test_kme_servers():
    """Test both KME servers directly"""
    print("🔬 DIRECT KME SERVER TESTING")
    print("=" * 50)
    
    # KME-1 Configuration (port 8010)
    kme1_client = OptimizedKMClient(
        base_url="https://127.0.0.1:8010",
        sae_id="25840139-0dd4-49ae-ba1e-b86731601803",
        ca_cert_path="../next-door-key-simulator/certs/ca.crt.pem",
        client_cert_path="../next-door-key-simulator/certs/sae-1.crt.pem", 
        client_key_path="../next-door-key-simulator/certs/sae-1.key.pem"
    )
    
    # KME-2 Configuration (port 8020)  
    kme2_client = OptimizedKMClient(
        base_url="https://127.0.0.1:8020",
        sae_id="c565d5aa-8670-4446-8471-b0e53e315d2a",
        ca_cert_path="../next-door-key-simulator/certs/ca.crt.pem",
        client_cert_path="../next-door-key-simulator/certs/sae-2.crt.pem",
        client_key_path="../next-door-key-simulator/certs/sae-2.key.pem"
    )
    
    print("\n🔍 Testing KME-1 (port 8010)...")
    try:
        # Test getting status of the OTHER SAE (KME-2's SAE)
        status1 = await kme1_client.check_key_status("c565d5aa-8670-4446-8471-b0e53e315d2a")
        print(f"   KME-1 status for KME-2's SAE: {status1}")
        
        # Try to get keys if available
        if status1.get('stored_key_count', 0) > 0:
            print(f"   🎉 KME-1 has {status1['stored_key_count']} keys available!")
            keys = await kme1_client.request_enc_keys("c565d5aa-8670-4446-8471-b0e53e315d2a", 256, 1)
            print(f"   ✅ Successfully got {len(keys)} keys from KME-1")
        else:
            print(f"   ⏳ KME-1 has no keys available yet")
            
    except Exception as e:
        print(f"   ❌ KME-1 error: {e}")
    
    print("\n🔍 Testing KME-2 (port 8020)...")
    try:
        # Test getting status of the OTHER SAE (KME-1's SAE)  
        status2 = await kme2_client.check_key_status("25840139-0dd4-49ae-ba1e-b86731601803")
        print(f"   KME-2 status for KME-1's SAE: {status2}")
        
        # Try to get keys if available
        if status2.get('stored_key_count', 0) > 0:
            print(f"   🎉 KME-2 has {status2['stored_key_count']} keys available!")
            keys = await kme2_client.request_enc_keys("25840139-0dd4-49ae-ba1e-b86731601803", 256, 1)
            print(f"   ✅ Successfully got {len(keys)} keys from KME-2")
        else:
            print(f"   ⏳ KME-2 has no keys available yet")
            
    except Exception as e:
        print(f"   ❌ KME-2 error: {e}")
    
    print("\n🕐 Waiting for key generation... (30 seconds)")
    await asyncio.sleep(30)
    
    print("\n🔄 Re-testing after waiting...")
    try:
        status1 = await kme1_client.check_key_status("c565d5aa-8670-4446-8471-b0e53e315d2a")
        status2 = await kme2_client.check_key_status("25840139-0dd4-49ae-ba1e-b86731601803")
        
        print(f"   KME-1 now has: {status1.get('stored_key_count', 0)} keys")
        print(f"   KME-2 now has: {status2.get('stored_key_count', 0)} keys")
        
        # Try actual key generation if available
        if status1.get('stored_key_count', 0) > 0:
            keys = await kme1_client.request_enc_keys("c565d5aa-8670-4446-8471-b0e53e315d2a", 256, 1) 
            print(f"   🎯 KME-1 key generation SUCCESS! Got key: {keys[0]['key_ID'][:16]}...")
            
        if status2.get('stored_key_count', 0) > 0:
            keys = await kme2_client.request_enc_keys("25840139-0dd4-49ae-ba1e-b86731601803", 256, 1)
            print(f"   🎯 KME-2 key generation SUCCESS! Got key: {keys[0]['key_ID'][:16]}...")
            
    except Exception as e:
        print(f"   ❌ Re-test error: {e}")
    
    # Cleanup
    await kme1_client.close()
    await kme2_client.close()
    
    print("\n✅ Direct KME testing complete!")

if __name__ == "__main__":
    asyncio.run(test_kme_servers())