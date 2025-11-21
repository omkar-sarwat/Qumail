"""Test if KME1 can discover KME2's SAE ID through network scanning"""
import requests
import time

def test_kme_discovery():
    print("Testing KME Network Discovery...")
    print("=" * 60)
    
    # Step 1: Check KME1 status
    print("\n1. Checking KME1 status...")
    kme1_response = requests.get("https://qumail-kme1-brzq.onrender.com/api/v1/kme/status")
    print(f"   KME1 Status: {kme1_response.status_code}")
    kme1_data = kme1_response.json()
    print(f"   KME1 SAE_ID: {kme1_data.get('SAE_ID')}")
    print(f"   KME1 Role: {kme1_data.get('role')}")
    
    # Step 2: Check KME2 status
    print("\n2. Checking KME2 status...")
    kme2_response = requests.get("https://qumail-kme2-brzq.onrender.com/api/v1/kme/status")
    print(f"   KME2 Status: {kme2_response.status_code}")
    kme2_data = kme2_response.json()
    print(f"   KME2 SAE_ID: {kme2_data.get('SAE_ID')}")
    print(f"   KME2 Role: {kme2_data.get('role')}")
    
    # Step 3: Try to get key status on KME1 for KME2's SAE
    print("\n3. Testing if KME1 can find KME2's SAE ID...")
    kme2_sae_id = kme2_data.get('SAE_ID')
    print(f"   Requesting key status for SAE: {kme2_sae_id}")
    
    try:
        status_response = requests.get(
            f"https://qumail-kme1-brzq.onrender.com/api/v1/keys/{kme2_sae_id}/status",
            timeout=10
        )
        print(f"   Status Check: {status_response.status_code}")
        if status_response.status_code == 200:
            print(f"   ✓ KME1 knows about KME2's SAE!")
            print(f"   Response: {status_response.json()}")
        else:
            print(f"   ✗ KME1 returned error: {status_response.text}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Step 4: Try to request encryption keys
    print("\n4. Testing enc_keys request...")
    try:
        enc_response = requests.post(
            f"https://qumail-kme1-brzq.onrender.com/api/v1/keys/{kme2_sae_id}/enc_keys",
            json={"number": 1, "size": 256},
            timeout=10
        )
        print(f"   Enc Keys Request: {enc_response.status_code}")
        if enc_response.status_code == 200:
            print(f"   ✓ Successfully got encryption keys!")
            data = enc_response.json()
            print(f"   Keys received: {len(data.get('keys', []))}")
        else:
            print(f"   ✗ Error: {enc_response.text}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n" + "=" * 60)
    print("Test complete!")

if __name__ == "__main__":
    test_kme_discovery()
