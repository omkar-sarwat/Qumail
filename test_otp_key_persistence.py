"""
Test script to verify OTP key persistence fix
Tests that keys generated during enc_keys are available for dec_keys
"""
import asyncio
import sys
import os

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'qumail-backend'))

from app.services.km_client_init import get_optimized_km_clients

async def test_key_persistence():
    """Test that keys persist from enc_keys to dec_keys"""
    print("="*80)
    print("TESTING OTP KEY PERSISTENCE FIX")
    print("="*80)
    
    # Get KM clients
    km1_client, km2_client = get_optimized_km_clients()
    
    # Test 1: Request encryption key from KME1
    print("\n[TEST 1] Requesting encryption key from KME1...")
    slave_sae_id = "c565d5aa-8670-4446-8471-b0e53e315d2a"
    
    try:
        enc_keys = await km1_client.request_enc_keys(
            slave_sae_id=slave_sae_id,
            number=1,
            size=256  # 256 bits
        )
        
        if not enc_keys:
            print("❌ FAILED: No encryption keys returned")
            return False
            
        key_id = enc_keys[0]['key_ID']
        print(f"✅ SUCCESS: Got encryption key {key_id}")
        
    except Exception as e:
        print(f"❌ FAILED: Error requesting enc_keys: {e}")
        return False
    
    # Test 2: Retrieve same key via dec_keys (should still be available)
    print(f"\n[TEST 2] Retrieving key {key_id} via dec_keys from KME2...")
    master_sae_id = "25840139-0dd4-49ae-ba1e-b86731601803"
    
    try:
        dec_keys = await km2_client.request_dec_keys(
            master_sae_id=master_sae_id,
            key_ids=[key_id]
        )
        
        if not dec_keys:
            print(f"❌ FAILED: Key {key_id} not found in dec_keys")
            return False
            
        print(f"✅ SUCCESS: Retrieved key {key_id} via dec_keys")
        
    except Exception as e:
        print(f"❌ FAILED: Error requesting dec_keys: {e}")
        return False
    
    # Test 3: Try to retrieve key again (should fail - OTP consumed)
    print(f"\n[TEST 3] Trying to retrieve key {key_id} again (should fail - OTP)...")
    
    try:
        dec_keys_again = await km2_client.request_dec_keys(
            master_sae_id=master_sae_id,
            key_ids=[key_id]
        )
        
        if dec_keys_again:
            print(f"❌ FAILED: Key {key_id} still available (OTP violation!)")
            return False
        else:
            print(f"✅ SUCCESS: Key {key_id} properly consumed (OTP enforced)")
            
    except Exception as e:
        # Expected to fail - key should be consumed
        print(f"✅ SUCCESS: Key {key_id} properly consumed (error: {e})")
    
    print("\n" + "="*80)
    print("ALL TESTS PASSED ✅")
    print("OTP key persistence is working correctly:")
    print("  1. Keys persist from enc_keys to dec_keys")
    print("  2. Keys are consumed after dec_keys (true OTP)")
    print("="*80)
    return True

if __name__ == "__main__":
    try:
        result = asyncio.run(test_key_persistence())
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"\n❌ TEST FAILED WITH EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
