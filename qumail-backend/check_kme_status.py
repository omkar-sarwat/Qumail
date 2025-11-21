#!/usr/bin/env python3
"""
Simple test to check if both KME servers are running
"""
import asyncio
import httpx
import ssl

async def test_kme_servers():
    """Test if both KME servers are accessible"""
    print("🔬 CHECKING KME SERVER STATUS")
    print("=" * 50)
    
    # Create SSL context that accepts self-signed certificates  
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    kme1_running = False
    kme2_running = False
    
    # Test KME-1 (port 8010)
    try:
        async with httpx.AsyncClient(verify=ssl_context, timeout=5.0) as client:
            response = await client.get("https://127.0.0.1:8010/api/v1/kme/status")
            if response.status_code == 200:
                data = response.json()
                print("✅ KME-1 (port 8010): RUNNING")
                print(f"   Status: {data}")
                kme1_running = True
            else:
                print(f"❌ KME-1: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ KME-1 (port 8010): NOT ACCESSIBLE - {type(e).__name__}: {e}")
    
    # Test KME-2 (port 8020)  
    try:
        async with httpx.AsyncClient(verify=ssl_context, timeout=5.0) as client:
            response = await client.get("https://127.0.0.1:8020/api/v1/kme/status")
            if response.status_code == 200:
                data = response.json()
                print("✅ KME-2 (port 8020): RUNNING") 
                print(f"   Status: {data}")
                kme2_running = True
            else:
                print(f"❌ KME-2: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ KME-2 (port 8020): NOT ACCESSIBLE - {type(e).__name__}: {e}")
    
    print("\n" + "="*50)
    
    if kme1_running and kme2_running:
        print("🎉 BOTH KME SERVERS ARE RUNNING!")
        print("   Key sharing should work between the servers.")
        print("   Now wait 30-60 seconds for key accumulation...")
    elif kme1_running or kme2_running:
        print("⚠️  ONLY ONE KME SERVER IS RUNNING!")
        print("   Both servers must be running for key sharing.")
        running = "KME-1" if kme1_running else "KME-2"
        not_running = "KME-2" if kme1_running else "KME-1"
        print(f"   ✅ {running} is running")
        print(f"   ❌ {not_running} needs to be started")
    else:
        print("❌ NEITHER KME SERVER IS RUNNING!")
        print("   You need to start both servers:")
        
    print("\n💡 To start the servers:")
    print("   Terminal 1: cd next-door-key-simulator ; copy .env.kme1 .env ; python app.py")
    print("   Terminal 2: cd next-door-key-simulator ; copy .env.kme2 .env ; python app.py")
    
    return kme1_running and kme2_running

if __name__ == "__main__":
    result = asyncio.run(test_kme_servers())
    if not result:
        exit(1)