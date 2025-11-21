"""Monitor Render deployment and test when ready"""
import requests
import time

def wait_for_deployment():
    print("Waiting for Render deployment...")
    print("=" * 60)
    print("This usually takes 2-3 minutes on Render free tier.")
    print("Checking every 15 seconds...\n")
    
    for i in range(20):  # Try for up to 5 minutes
        time.sleep(15)
        
        try:
            # Check both KMEs
            kme1 = requests.get("https://qumail-kme1-brzq.onrender.com/api/v1/kme/status", timeout=10)
            kme2 = requests.get("https://qumail-kme2-brzq.onrender.com/api/v1/kme/status", timeout=10)
            
            if kme1.status_code == 200 and kme2.status_code == 200:
                print(f"✓ Both KMEs are online! (attempt {i+1})")
                
                # Now test enc_keys
                print("\nTesting enc_keys request...")
                kme2_data = kme2.json()
                kme2_sae_id = kme2_data.get('SAE_ID')
                
                enc_response = requests.post(
                    f"https://qumail-kme1-brzq.onrender.com/api/v1/keys/{kme2_sae_id}/enc_keys",
                    json={"number": 1, "size": 256},
                    timeout=70  # Allow time for broadcast
                )
                
                if enc_response.status_code == 200:
                    print(f"✓ SUCCESS! Encryption keys retrieved successfully!")
                    data = enc_response.json()
                    print(f"  Keys received: {len(data.get('keys', []))}")
                    if data.get('keys'):
                        print(f"  First key ID: {data['keys'][0].get('key_ID')}")
                    return True
                else:
                    print(f"✗ Still getting error {enc_response.status_code}")
                    print(f"  Response: {enc_response.text[:200]}")
            else:
                print(f"Waiting... KME1: {kme1.status_code}, KME2: {kme2.status_code}")
                
        except Exception as e:
            print(f"Waiting... Error: {str(e)[:100]}")
    
    print("\n✗ Deployment timed out after 5 minutes")
    return False

if __name__ == "__main__":
    success = wait_for_deployment()
    if success:
        print("\n" + "=" * 60)
        print("KME servers are ready! You can now test encrypted email.")
        print("=" * 60)
    else:
        print("\nPlease check Render dashboard for deployment status.")
