"""Diagnostic script to check quantum key synchronization between KM1 and KM2"""
import requests
import json
import time
import urllib3

# Disable SSL warnings for testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Render URLs
KME1_URL = "https://qumail-kme1-brzq.onrender.com"
KME2_URL = "https://qumail-kme2-brzq.onrender.com"

print("="*80)
print("QUANTUM KEY SYNCHRONIZATION DIAGNOSTIC (RENDER)")
print("="*80)
print()

# Check KME1 status
print(f"Checking KME1 ({KME1_URL})...")
try:
    r1 = requests.get(f"{KME1_URL}/api/v1/kme/status", verify=False)
    km1_status = r1.json()
    print(f"✅ KME1 Status: {json.dumps(km1_status, indent=2)}")
    km1_sae = km1_status.get('SAE_ID')
except Exception as e:
    print(f"❌ Failed to get KME1 status: {e}")
    km1_sae = None

print()

# Check KME2 status
print(f"Checking KME2 ({KME2_URL})...")
try:
    r2 = requests.get(f"{KME2_URL}/api/v1/kme/status", verify=False)
    km2_status = r2.json()
    print(f"✅ KME2 Status: {json.dumps(km2_status, indent=2)}")
    km2_sae = km2_status.get('SAE_ID')
except Exception as e:
    print(f"❌ Failed to get KME2 status: {e}")
    km2_sae = None

print()
print("="*80)

if km1_sae and km2_sae:
    print(f"KM1 SAE ID: {km1_sae}")
    print(f"KM2 SAE ID: {km2_sae}")
    print()
    
    # 1. Request Encryption Keys from KME1 (Simulate Sender)
    print("TEST 1: Requesting Encryption Keys from KME1 (Sender Flow)...")
    key_id = None
    try:
        # Request keys for communication with KME2
        payload = {
            "number": 1,
            "size": 256  # bits
        }
        # POST /api/v1/keys/{slave_sae_id}/enc_keys
        url = f"{KME1_URL}/api/v1/keys/{km2_sae}/enc_keys"
        print(f"POST {url}")
        r = requests.post(url, json=payload, verify=False)
        
        if r.status_code == 200:
            data = r.json()
            keys = data.get('keys', [])
            if keys:
                key_id = keys[0]['key_ID']
                print(f"✅ Generated Key on KME1: {key_id}")
            else:
                print("❌ No keys returned in response")
        else:
            print(f"❌ Failed to generate keys: {r.status_code} - {r.text}")
            
    except Exception as e:
        print(f"❌ Exception during generation: {e}")

    print()
    
    # 2. Retrieve Decryption Key from KME2 (Simulate Receiver)
    if key_id:
        print(f"TEST 2: Retrieving Key {key_id} from KME2 (Receiver Flow)...")
        # Wait a moment for sync (though shared pool should be instant)
        time.sleep(2)
        
        try:
            # POST /api/v1/keys/{master_sae_id}/dec_keys
            # KME2 is the slave, KME1 is the master
            url = f"{KME2_URL}/api/v1/keys/{km1_sae}/dec_keys"
            payload = {
                "key_IDs": [{"key_ID": key_id}]
            }
            print(f"POST {url}")
            r = requests.post(url, json=payload, verify=False)
            
            if r.status_code == 200:
                data = r.json()
                keys = data.get('keys', [])
                if keys and keys[0]['key_ID'] == key_id:
                    print(f"✅ SUCCESS: Retrieved Key {key_id} from KME2!")
                    print("   (This confirms KME1 and KME2 are sharing the key pool correctly)")
                else:
                    print(f"❌ Failed: Key not found in response. Keys: {keys}")
            else:
                print(f"❌ Failed to retrieve key: {r.status_code} - {r.text}")
                
        except Exception as e:
            print(f"❌ Exception during retrieval: {e}")
            
    # 3. Retrieve Decryption Key from KME1 (Shared Pool Check)
    if key_id:
        print()
        print(f"TEST 3: Retrieving Key {key_id} directly from KME1 (Shared Pool Check)...")
        try:
            url = f"{KME1_URL}/api/v1/keys/{km1_sae}/dec_keys" # Self-check? Or check as slave?
            # Actually, for shared pool, we can check if KME1 can retrieve it too
            # But usually KME1 is master. Let's try retrieving it as if we were KME2 asking KME1
            
            # Actually, let's just check if KME1 has it in its store
            url = f"{KME1_URL}/api/v1/keys/{km2_sae}/status"
            r = requests.get(url, verify=False)
            print(f"KME1 Key Status for {km2_sae}: {r.text}")
            
        except Exception as e:
            print(f"❌ Exception: {e}")

print()
print("="*80)
