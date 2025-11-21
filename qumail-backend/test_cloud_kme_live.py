"""
Test connectivity to live cloud KME servers on Render.com
"""
import asyncio
import aiohttp
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

KME1_URL = os.getenv("KM1_BASE_URL", "https://qumail-kme1-brzq.onrender.com")
KME2_URL = os.getenv("KM2_BASE_URL", "https://qumail-kme2-brzq.onrender.com")

async def test_kme_health(url: str, name: str):
    """Test KME health endpoint"""
    print(f"\n{'='*60}")
    print(f"Testing {name}: {url}")
    print(f"{'='*60}")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test health/status endpoint
            status_url = f"{url}/api/v1/kme/status"
            print(f"\n📡 Checking status endpoint: {status_url}")
            
            async with session.get(status_url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                print(f"✅ Status Code: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Response:")
                    print(f"   KME ID: {data.get('kme_id', 'N/A')}")
                    print(f"   Status: {data.get('status', 'N/A')}")
                    print(f"   Available Keys: {data.get('available_keys', 'N/A')}")
                    print(f"   SAE ID: {data.get('attached_sae_id', 'N/A')}")
                    return True
                else:
                    text = await response.text()
                    print(f"❌ Error response: {text}")
                    return False
                    
    except asyncio.TimeoutError:
        print(f"❌ Timeout - KME server may be sleeping (cold start)")
        print(f"   Free tier servers sleep after 15 min inactivity")
        print(f"   First request takes 30-60 seconds to wake up")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

async def test_key_generation(url: str, name: str, slave_sae_id: str):
    """Test key generation endpoint"""
    print(f"\n{'='*60}")
    print(f"Testing Key Generation - {name}")
    print(f"{'='*60}")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Request encryption keys
            enc_keys_url = f"{url}/api/v1/keys/{slave_sae_id}/enc_keys"
            print(f"\n🔑 Requesting keys from: {enc_keys_url}")
            print(f"   Slave SAE ID: {slave_sae_id}")
            
            # Make POST request with proper headers
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            payload = {
                "number": 1,  # Request 1 key
                "size": 256   # 256 bits = 32 bytes
            }
            
            async with session.post(
                enc_keys_url, 
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                print(f"✅ Status Code: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Keys retrieved successfully!")
                    print(f"   Keys received: {len(data.get('keys', []))}")
                    if data.get('keys'):
                        key = data['keys'][0]
                        print(f"   Key ID: {key.get('key_ID', 'N/A')}")
                        print(f"   Key size: {len(key.get('key', ''))} chars (base64)")
                    return True
                else:
                    text = await response.text()
                    print(f"❌ Error response: {text}")
                    return False
                    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

async def main():
    """Main test function"""
    print("\n" + "="*60)
    print("🔐 QuMail Cloud KME Connection Test")
    print("="*60)
    print(f"\n📍 KME 1 URL: {KME1_URL}")
    print(f"📍 KME 2 URL: {KME2_URL}")
    
    # Test KME 1 (Sender)
    kme1_health = await test_kme_health(KME1_URL, "KME 1 (Sender)")
    await asyncio.sleep(2)
    
    # Test KME 2 (Receiver)
    kme2_health = await test_kme_health(KME2_URL, "KME 2 (Receiver)")
    await asyncio.sleep(2)
    
    # If health checks pass, test key generation
    if kme1_health:
        # KME1 generates keys for SAE ID of KME2
        await test_key_generation(
            KME1_URL, 
            "KME 1 → KME 2",
            "c565d5aa-8670-4446-8471-b0e53e315d2a"  # KME2's SAE ID
        )
    
    if kme2_health:
        # KME2 retrieves keys for SAE ID of KME1
        await test_key_generation(
            KME2_URL,
            "KME 2 → KME 1", 
            "25840139-0dd4-49ae-ba1e-b86731601803"  # KME1's SAE ID
        )
    
    print("\n" + "="*60)
    print("✅ Test Complete!")
    print("="*60)
    
    if kme1_health and kme2_health:
        print("\n✅ Both KME servers are operational and reachable!")
        print("✅ Your QuMail backend can now use these cloud KME servers for quantum encryption.")
        print("\n📝 Next steps:")
        print("   1. Restart your backend: python -m uvicorn app.main:app --reload")
        print("   2. Test encryption from frontend")
        print("   3. Monitor KME server logs on Render dashboard")
    else:
        print("\n⚠️ Some KME servers are not responding")
        print("   This is normal if servers are sleeping (free tier)")
        print("   Wait 60 seconds and try again")

if __name__ == "__main__":
    asyncio.run(main())
