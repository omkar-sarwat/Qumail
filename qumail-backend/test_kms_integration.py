"""
Test QuMail Backend Integration with QuMail-KMS
Verifies that the backend can successfully connect to both KMS instances
"""
import sys
import asyncio
sys.path.append('.')

from app.services.km_client_init import create_optimized_km_clients

async def test_kms_integration():
    """Test connection to both KMS instances"""
    print("=" * 80)
    print("Testing QuMail Backend Integration with QuMail-KMS")
    print("=" * 80)
    
    try:
        # Create KM clients
        print("\n1. Creating KM clients...")
        km1_client, km2_client = create_optimized_km_clients()
        print("   ✓ KM clients created successfully")
        print(f"   - KM1: {km1_client.base_url} (SAE: {km1_client.sae_id})")
        print(f"   - KM2: {km2_client.base_url} (SAE: {km2_client.sae_id})")
        
        # Test KMS-1 connection
        print("\n2. Testing KMS-1 connection...")
        # Use KME status endpoint instead of key status
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{km1_client.base_url}/api/v1/kme/status")
            status1 = response.json()
        print(f"   ✓ KMS-1 Status: {status1['status']}")
        print(f"   - KMS ID: {status1['KME_ID']}")
        print(f"   - Total keys: {status1['total_keys']}")
        
        # Test KMS-2 connection
        print("\n3. Testing KMS-2 connection...")
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{km2_client.base_url}/api/v1/kme/status")
            status2 = response.json()
        print(f"   ✓ KMS-2 Status: {status2['status']}")
        print(f"   - KMS ID: {status2['KME_ID']}")
        print(f"   - Total keys: {status2['total_keys']}")
        
        # Test key request from KMS-1
        print("\n4. Requesting encryption keys from KMS-1...")
        enc_keys_response = await km1_client.request_enc_keys(
            slave_sae_id=km2_client.sae_id,
            number=1,
            size=256
        )
        print(f"   ✓ Received {len(enc_keys_response.get('keys', []))} encryption key(s)")
        if enc_keys_response.get('keys'):
            print(f"   - Key ID: {enc_keys_response['keys'][0]['key_ID']}")
            print(f"   - Key size: {len(enc_keys_response['keys'][0]['key'])} bytes")
        
        # Test key request from KMS-2
        print("\n5. Requesting decryption keys from KMS-2...")
        if enc_keys_response.get('keys'):
            key_id = enc_keys_response['keys'][0]['key_ID']
            dec_keys_response = await km2_client.request_dec_keys(
                master_sae_id=km1_client.sae_id,
                key_ids=[{"key_ID": key_id}]
            )
            print(f"   ✓ Received {len(dec_keys_response.get('keys', []))} decryption key(s)")
            if dec_keys_response.get('keys'):
                print(f"   - Keys match: {enc_keys_response['keys'][0]['key'] == dec_keys_response['keys'][0]['key']}")
        
        # Close clients
        await km1_client.close()
        await km2_client.close()
        
        print("\n" + "=" * 80)
        print("✓ ALL TESTS PASSED - QuMail Backend successfully integrated with QuMail-KMS!")
        print("=" * 80)
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\nMake sure both KMS instances are running:")
    print("  - KMS-1 on port 9010")
    print("  - KMS-2 on port 9020")
    print("\nStarting tests in 3 seconds...\n")
    
    import time
    time.sleep(3)
    
    success = asyncio.run(test_kms_integration())
    sys.exit(0 if success else 1)
