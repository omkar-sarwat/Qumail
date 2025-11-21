#!/usr/bin/env python3
"""
Test if both KME servers are running and communicating
"""
import asyncio
import httpx

async def test_both_kme_servers():
    """Test if both KME servers are running"""
    print("🔬 TESTING BOTH KME SERVERS")
    print("=" * 40)
    
    # Test KME-1 (port 8010)
    try:
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.get("https://127.0.0.1:8010/api/v1/kme/status", timeout=5.0)
            if response.status_code == 200:
                print("✅ KME-1 (port 8010) is RUNNING")
                data = response.json()
                print(f"   KME-1 Status: {data}")
            else:
                print(f"❌ KME-1 returned {response.status_code}")
    except Exception as e:
        print(f"❌ KME-1 (port 8010) is NOT RUNNING: {e}")
    
    # Test KME-2 (port 8020)  
    try:
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.get("https://127.0.0.1:8020/api/v1/kme/status", timeout=5.0)
            if response.status_code == 200:
                print("✅ KME-2 (port 8020) is RUNNING") 
                data = response.json()
                print(f"   KME-2 Status: {data}")
            else:
                print(f"❌ KME-2 returned {response.status_code}")
    except Exception as e:
        print(f"❌ KME-2 (port 8020) is NOT RUNNING: {e}")
    
    print("\n💡 Both KME servers must be running for key sharing to work!")
    print("   Start them in separate terminals:")
    print("   Terminal 1: cd next-door-key-simulator ; copy .env.kme1 .env ; python app.py")  
    print("   Terminal 2: cd next-door-key-simulator ; copy .env.kme2 .env ; python app.py")

if __name__ == "__main__":
    asyncio.run(test_both_kme_servers())