#!/usr/bin/env python3
"""
Test script to verify receiver identification with KME key tracking.

This tests the flow:
1. Sender requests encryption key from KME1 with X-Sender-Email and X-Receiver-Email headers
2. KME stores the email association with the key
3. Receiver requests decryption key from KME2 with X-Receiver-Email header
4. KME verifies the receiver matches the intended recipient
"""

import requests
import json
import base64
import time
import os

# Configuration
KME1_URL = os.getenv("KME1_URL", "http://127.0.0.1:8010")
KME2_URL = os.getenv("KME2_URL", "http://127.0.0.1:8020")

# SAE IDs (from the standard configuration)
KM1_SAE_ID = "25840139-0dd4-49ae-ba1e-b86731601803"
KM2_SAE_ID = "c565d5aa-8670-4446-8471-b0e53e315d2a"

def print_header(title):
    print("\n" + "="*70)
    print(f" {title}")
    print("="*70)

def test_enc_keys_with_email_tracking():
    """Test requesting encryption keys with sender/receiver email headers."""
    print_header("TEST: Request Encryption Keys with Email Tracking")
    
    sender_email = "alice@qumail.test"
    receiver_email = "bob@qumail.test"
    
    url = f"{KME1_URL}/api/v1/keys/{KM2_SAE_ID}/enc_keys"
    headers = {
        "X-SAE-ID": KM1_SAE_ID,
        "X-Sender-Email": sender_email,
        "X-Receiver-Email": receiver_email,
        "Content-Type": "application/json"
    }
    
    # Request 1 key of 256 bits
    data = {"number": 1, "size": 256}
    
    print(f"  URL: {url}")
    print(f"  Headers: X-Sender-Email={sender_email}, X-Receiver-Email={receiver_email}")
    print(f"  Request: {data}")
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            keys = result.get("keys", [])
            
            if keys:
                key_id = keys[0].get("key_ID", "N/A")
                key_data = keys[0].get("key", "N/A")[:32] + "..."
                print(f"  ✓ Got {len(keys)} key(s)")
                print(f"    Key ID: {key_id[:32]}...")
                print(f"    Key Data: {key_data}")
                print(f"    Receiver SAE ID: {result.get('receiver_sae_id', 'N/A')}")
                print(f"    Receiver Email: {result.get('receiver_email', 'N/A')}")
                print(f"    Sender Email: {result.get('sender_email', 'N/A')}")
                return True, key_id
            else:
                print(f"  ✗ No keys returned")
                return False, None
        else:
            print(f"  ✗ Error: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"  ✗ Exception: {e}")
        return False, None

def test_dec_keys_with_receiver_verification(key_id, receiver_email="bob@qumail.test"):
    """Test requesting decryption keys with receiver email verification."""
    print_header("TEST: Request Decryption Keys with Receiver Verification")
    
    url = f"{KME2_URL}/api/v1/keys/{KM1_SAE_ID}/dec_keys"
    headers = {
        "X-SAE-ID": KM2_SAE_ID,
        "X-Receiver-Email": receiver_email,
        "Content-Type": "application/json"
    }
    params = {"key_ID": key_id}
    
    print(f"  URL: {url}")
    print(f"  Key ID: {key_id[:32]}...")
    print(f"  Receiver Email: {receiver_email}")
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            keys = result.get("keys", [])
            
            if keys:
                retrieved_key_id = keys[0].get("key_ID", "N/A")
                print(f"  ✓ Got {len(keys)} key(s)")
                print(f"    Key ID: {retrieved_key_id[:32]}...")
                return True
            else:
                print(f"  ✗ No keys returned")
                return False
        elif response.status_code == 206:
            # Partial result
            print(f"  ⚠ Partial result: {response.text}")
            return True
        else:
            print(f"  ✗ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"  ✗ Exception: {e}")
        return False

def test_key_email_association():
    """Test that keys are properly associated with emails in KeyStore."""
    print_header("TEST: Key-Email Association in KeyStore")
    
    # This test requires access to KME's internal state, which we can check via logs
    # For now, we just verify the API accepts and logs the headers
    
    sender_email = "charlie@qumail.test"
    receiver_email = "diana@qumail.test"
    
    url = f"{KME1_URL}/api/v1/keys/{KM2_SAE_ID}/enc_keys"
    headers = {
        "X-SAE-ID": KM1_SAE_ID,
        "X-Sender-Email": sender_email,
        "X-Receiver-Email": receiver_email,
        "Content-Type": "application/json"
    }
    data = {"number": 1, "size": 256}
    
    print(f"  Sender: {sender_email}")
    print(f"  Receiver: {receiver_email}")
    print("  (Check KME terminal logs for '[KEY_STORE] Associated key...' messages)")
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"  ✓ Request successful")
            print(f"    Sender in response: {result.get('sender_email', 'N/A')}")
            print(f"    Receiver in response: {result.get('receiver_email', 'N/A')}")
            return True
        else:
            print(f"  ✗ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"  ✗ Exception: {e}")
        return False

def run_all_tests():
    """Run all receiver identification tests."""
    print("\n" + "#"*70)
    print("# RECEIVER IDENTIFICATION TESTS")
    print("# Testing KME key tracking with sender/receiver email association")
    print("#"*70)
    
    results = {}
    
    # Test 1: Request encryption keys with email tracking
    success, key_id = test_enc_keys_with_email_tracking()
    results["enc_keys_with_email"] = success
    
    if success and key_id:
        # Wait a moment for key to propagate
        time.sleep(0.5)
        
        # Test 2: Request decryption keys with receiver verification
        success = test_dec_keys_with_receiver_verification(key_id)
        results["dec_keys_with_verification"] = success
    else:
        results["dec_keys_with_verification"] = False
    
    # Test 3: Key-email association
    success = test_key_email_association()
    results["key_email_association"] = success
    
    # Summary
    print_header("TEST SUMMARY")
    all_passed = True
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {test_name}: {status}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("  🎉 All tests passed!")
    else:
        print("  ❌ Some tests failed. Check KME logs for details.")
    
    return all_passed

if __name__ == "__main__":
    run_all_tests()
