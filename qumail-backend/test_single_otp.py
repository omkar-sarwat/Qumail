"""Test single Level 1 OTP encryption and decryption with detailed logging"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

print("="*80)
print("LEVEL 1 OTP SINGLE EMAIL TEST WITH DETAILED KEY TRACKING")
print("="*80)
print()

# Step 1: Authenticate
print("Step 1: Authenticating...")
auth_response = requests.post(f"{BASE_URL}/api/auth/login", json={
    "email": "test@example.com",
    "password": "test123"
})
token = auth_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print(f"✅ Authenticated")
print()

# Step 2: Send encrypted email (Level 1)
print("Step 2: Sending Level 1 OTP encrypted email...")
email_data = {
    "subject": f"Test OTP Email - {time.strftime('%Y-%m-%d %H:%M:%S')}",
    "body": "This is a test message for Level 1 OTP encryption with quantum keys!",
    "recipient": "recipient@example.com",
    "security_level": 1
}

send_response = requests.post(f"{BASE_URL}/api/emails/send", json=email_data, headers=headers)
send_result = send_response.json()

if send_response.status_code != 200:
    print(f"❌ Failed to send email: {send_result}")
    exit(1)

email_uuid = send_result["uuid"]
key_id = send_result.get("key_id")
flow_id = send_result.get("flow_id")

print(f"✅ Email sent successfully")
print(f"   Email UUID: {email_uuid}")
print(f"   Key ID: {key_id}")
print(f"   Flow ID: {flow_id}")
print()

# Step 3: Wait a bit for key synchronization
print("Step 3: Waiting 2 seconds for key synchronization...")
time.sleep(2)
print()

# Step 4: Check if key exists on KM2
print("Step 4: Checking if key exists on KM2...")
try:
    # Try to get the key from KM2 using dec_keys endpoint
    dec_request = {
        "key_IDs": [{"key_ID": key_id}]
    }
    headers_km2 = {"X-SAE-ID": "c565d5aa-8670-4446-8471-b0e53e315d2a"}
    
    km2_response = requests.post(
        "http://127.0.0.1:8020/api/v1/keys/25840139-0dd4-49ae-ba1e-b86731601803/dec_keys",
        json=dec_request,
        headers=headers_km2
    )
    
    if km2_response.status_code == 200:
        print(f"✅ Key found on KM2!")
        print(f"   Response: {km2_response.json()}")
    elif km2_response.status_code == 404:
        print(f"❌ Key NOT found on KM2")
        print(f"   Key ID requested: {key_id}")
        print(f"   Response: {km2_response.json()}")
    else:
        print(f"⚠️  Unexpected response from KM2: {km2_response.status_code}")
        print(f"   Response: {km2_response.text}")
except Exception as e:
    print(f"❌ Failed to check KM2: {e}")

print()

# Step 5: Try to decrypt
print("Step 5: Attempting to decrypt email...")
decrypt_response = requests.get(f"{BASE_URL}/api/emails/{email_uuid}/decrypt", headers=headers)

if decrypt_response.status_code == 200:
    decrypt_result = decrypt_response.json()
    print(f"✅ Email decrypted successfully!")
    print(f"   Decrypted body: {decrypt_result.get('body', '')[:100]}...")
elif decrypt_response.status_code == 500:
    print(f"❌ Decryption failed")
    error_detail = decrypt_response.json().get('detail', 'Unknown error')
    print(f"   Error: {error_detail}")
else:
    print(f"⚠️  Unexpected response: {decrypt_response.status_code}")
    print(f"   Response: {decrypt_response.text[:200]}")

print()
print("="*80)
print("TEST COMPLETE")
print("="*80)
