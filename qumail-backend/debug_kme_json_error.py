#!/usr/bin/env python3
"""
Debug script to find the source of JSON parse error in generate-keys endpoint
"""
import asyncio
import sys
sys.path.insert(0, '.')

async def test_kme_clients():
    """Test KME clients directly to see where JSON error occurs"""
    print("Testing KME clients directly...")
    
    try:
        from app.services.km_client_init import get_optimized_km_clients
        
        km_client1, km_client2 = get_optimized_km_clients()
        print(f"✅ KM clients initialized")
        print(f"  KME1: {km_client1.base_url}")
        print(f"  KME2: {km_client2.base_url}")
        
        # Test KME1 check_key_status
        print("\nTesting KME1 check_key_status...")
        try:
            result1 = await km_client1.check_key_status("c565d5aa-8670-4446-8471-b0e53e315d2a")
            print(f"✅ KME1 check_key_status succeeded")
            print(f"  Response type: {type(result1)}")
            print(f"  Response: {result1}")
        except Exception as e:
            print(f"❌ KME1 check_key_status failed: {e}")
            print(f"  Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
        
        # Test KME2 check_key_status
        print("\nTesting KME2 check_key_status...")
        try:
            result2 = await km_client2.check_key_status("25840139-0dd4-49ae-ba1e-b86731601803")
            print(f"✅ KME2 check_key_status succeeded")
            print(f"  Response type: {type(result2)}")
            print(f"  Response: {result2}")
        except Exception as e:
            print(f"❌ KME2 check_key_status failed: {e}")
            print(f"  Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ Failed to initialize KM clients: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_kme_clients())
