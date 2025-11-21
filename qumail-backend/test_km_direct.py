"""Test KM client directly to debug key fetching"""
import asyncio
import sys
sys.path.insert(0, '.')

async def test_km_fetch():
    from app.services.km_client_init import get_optimized_km_clients
    
    print("Getting KM clients...")
    km1_client, km2_client = get_optimized_km_clients()
    
    print(f"KM1 client: {km1_client.base_url}")
    print(f"KM2 client: {km2_client.base_url}")
    
    try:
        print("\n🔍 Testing KM1 enc_keys request...")
        km1_keys = await km1_client.request_enc_keys(
            slave_sae_id="c565d5aa-8670-4446-8471-b0e53e315d2a",
            number=1,
            size=256
        )
        print(f"✅ KM1 returned {len(km1_keys)} keys")
        print(f"   Key ID: {km1_keys[0]['key_ID']}")
        
    except Exception as e:
        print(f"❌ KM1 Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        print("\n🔍 Testing KM2 enc_keys request...")
        km2_keys = await km2_client.request_enc_keys(
            slave_sae_id="25840139-0dd4-49ae-ba1e-b86731601803",
            number=1,
            size=256
        )
        print(f"✅ KM2 returned {len(km2_keys)} keys")
        print(f"   Key ID: {km2_keys[0]['key_ID']}")
        
    except Exception as e:
        print(f"❌ KM2 Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_km_fetch())
