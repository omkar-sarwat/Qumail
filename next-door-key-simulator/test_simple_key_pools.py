"""
Simple Test for User Key Pools

Verifies basic functionality of the per-user key pool system.
Run this after starting the KME server.
"""
import os
import sys
import json
import base64
import requests

# Configuration
BASE_URL = os.getenv('KME_BASE_URL', 'http://localhost:8010')
API_URL = f"{BASE_URL}/api/v1/keys"

# Key size constant
KEY_SIZE_BYTES = 1024
KEY_SIZE_BITS = KEY_SIZE_BYTES * 8

# Test users
ALICE_SAE_ID = "SAE_TEST_ALICE_001"
BOB_SAE_ID = "SAE_TEST_BOB_001"


def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")


def print_result(test_name, passed, details=""):
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"  {status}: {test_name}")
    if details and not passed:
        print(f"      Details: {details}")


def cleanup():
    """Clean up test users."""
    print_header("Cleanup")
    try:
        requests.delete(f"{API_URL}/{ALICE_SAE_ID}", timeout=5)
        requests.delete(f"{API_URL}/{BOB_SAE_ID}", timeout=5)
        print("  Cleaned up test users")
    except:
        print("  No cleanup needed")


def test_registration():
    """Test user registration."""
    print_header("Test 1: User Registration")
    
    # Register Alice
    result = requests.post(f"{API_URL}/register", json={
        "sae_id": ALICE_SAE_ID,
        "user_email": "alice.test@example.com",
        "initial_pool_size": 50
    }, timeout=10)
    
    passed = result.status_code == 201
    data = result.json()
    print_result(f"Register Alice (status: {result.status_code})", passed,
                 data.get('error', ''))
    
    if passed:
        print(f"      Keys generated: {data.get('keys_generated')}")
    
    # Register Bob
    result = requests.post(f"{API_URL}/register", json={
        "sae_id": BOB_SAE_ID,
        "user_email": "bob.test@example.com",
        "initial_pool_size": 50
    }, timeout=10)
    
    passed = result.status_code == 201
    data = result.json()
    print_result(f"Register Bob (status: {result.status_code})", passed,
                 data.get('error', ''))
    
    return passed


def test_key_size():
    """Test that keys are exactly 1KB."""
    print_header("Test 2: Key Size Validation (1KB)")
    
    # Get a key from Bob's pool
    result = requests.post(f"{API_URL}/{BOB_SAE_ID}/enc_keys",
                          json={"number": 1, "size": KEY_SIZE_BITS},
                          headers={"X-SAE-ID": ALICE_SAE_ID},
                          timeout=10)
    
    if result.status_code != 200:
        print_result("Get key", False, f"Status: {result.status_code}")
        return False
    
    data = result.json()
    keys = data.get('keys', [])
    
    if not keys:
        print_result("Key received", False, "No keys returned")
        return False
    
    key_b64 = keys[0].get('key', '')
    key_bytes = base64.b64decode(key_b64)
    key_size = len(key_bytes)
    
    passed = key_size == KEY_SIZE_BYTES
    print_result(f"Key size: {key_size} bytes (expected: {KEY_SIZE_BYTES})", passed)
    print(f"      Key ID: {keys[0].get('key_ID')}")
    
    return passed


def test_cross_user_key_request():
    """Test that sender requests keys from receiver's pool."""
    print_header("Test 3: Cross-User Key Request")
    
    # Get Bob's pool status before
    bob_before = requests.get(f"{API_URL}/{BOB_SAE_ID}/status", timeout=5).json()
    bob_available_before = bob_before.get('available_keys', 0)
    
    # Alice requests 3 keys from Bob's pool
    result = requests.post(f"{API_URL}/{BOB_SAE_ID}/enc_keys",
                          json={"number": 3, "size": KEY_SIZE_BITS},
                          headers={"X-SAE-ID": ALICE_SAE_ID},
                          timeout=10)
    
    passed = result.status_code == 200
    data = result.json()
    keys = data.get('keys', [])
    
    print_result(f"Alice got {len(keys)} keys from Bob's pool", len(keys) == 3)
    
    # Get Bob's pool status after
    bob_after = requests.get(f"{API_URL}/{BOB_SAE_ID}/status", timeout=5).json()
    bob_available_after = bob_after.get('available_keys', 0)
    
    decrease = bob_available_before - bob_available_after
    print_result(f"Bob's pool decreased by {decrease} keys", decrease >= 3,
                 f"Before: {bob_available_before}, After: {bob_available_after}")
    
    # Verify Alice's pool unchanged
    alice_status = requests.get(f"{API_URL}/{ALICE_SAE_ID}/status", timeout=5).json()
    alice_available = alice_status.get('available_keys', 0)
    print_result(f"Alice's pool unchanged at {alice_available} keys", alice_available == 50)
    
    return passed and decrease >= 3


def test_decryption_keys():
    """Test retrieving keys by ID for decryption."""
    print_header("Test 4: Decryption Keys")
    
    # Get encryption keys
    enc_result = requests.post(f"{API_URL}/{ALICE_SAE_ID}/enc_keys",
                              json={"number": 2, "size": KEY_SIZE_BITS},
                              headers={"X-SAE-ID": BOB_SAE_ID},
                              timeout=10)
    
    if enc_result.status_code != 200:
        print_result("Get encryption keys", False)
        return False
    
    enc_data = enc_result.json()
    key_ids = [k.get('key_ID') for k in enc_data.get('keys', [])]
    
    print_result(f"Got {len(key_ids)} encryption keys", len(key_ids) == 2)
    
    # Retrieve same keys for decryption
    dec_result = requests.post(f"{API_URL}/{BOB_SAE_ID}/dec_keys",
                              json={"key_IDs": [{"key_ID": kid} for kid in key_ids]},
                              headers={"X-SAE-ID": ALICE_SAE_ID},
                              timeout=10)
    
    dec_data = dec_result.json()
    dec_keys = dec_data.get('keys', [])
    
    passed = len(dec_keys) == len(key_ids)
    print_result(f"Retrieved {len(dec_keys)} decryption keys", passed)
    
    return passed


def test_pool_status():
    """Test pool status endpoint."""
    print_header("Test 5: Pool Status")
    
    result = requests.get(f"{API_URL}/{ALICE_SAE_ID}/status", timeout=5)
    
    passed = result.status_code == 200
    data = result.json()
    
    print_result("Status endpoint returns 200", passed)
    
    if passed:
        print(f"      SAE ID: {data.get('sae_id')}")
        print(f"      Total keys: {data.get('total_keys')}")
        print(f"      Available: {data.get('available_keys')}")
        print(f"      Used: {data.get('used_keys')}")
        print(f"      Key size: {data.get('key_size')} bits")
    
    return passed


def test_refill():
    """Test pool refill."""
    print_header("Test 6: Pool Refill")
    
    # First, consume some keys from Alice's pool so we can refill
    # Bob requests 10 keys from Alice's pool
    consume_result = requests.post(f"{API_URL}/{ALICE_SAE_ID}/enc_keys",
                                   json={"number": 10, "size": KEY_SIZE_BITS},
                                   headers={"X-SAE-ID": BOB_SAE_ID},
                                   timeout=10)
    
    if consume_result.status_code != 200:
        print_result("Consume keys before refill", False, "Failed to consume keys")
        return False
    
    print_result("Consumed 10 keys from Alice's pool", True)
    
    # Get current status after consumption
    before = requests.get(f"{API_URL}/{ALICE_SAE_ID}/status", timeout=5).json()
    available_before = before.get('available_keys', 0)
    print(f"      Available before refill: {available_before}")
    
    # Request refill
    result = requests.post(f"{API_URL}/{ALICE_SAE_ID}/refill",
                          json={"keys_to_add": 10},
                          timeout=10)
    
    passed = result.status_code == 200
    data = result.json()
    
    print_result("Refill request accepted", passed)
    
    if passed:
        print(f"      Keys added: {data.get('keys_added')}")
    
    # Verify increase
    after = requests.get(f"{API_URL}/{ALICE_SAE_ID}/status", timeout=5).json()
    available_after = after.get('available_keys', 0)
    
    increased = available_after > available_before
    print_result(f"Pool increased from {available_before} to {available_after}", increased)
    
    return passed and increased


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("  Per-User Key Pool Simple Test Suite")
    print("="*60)
    print(f"\n  Target: {BASE_URL}")
    
    # Check server health
    try:
        health = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"  Server health: {health.status_code}")
    except Exception as e:
        print(f"  ERROR: Cannot connect to server at {BASE_URL}")
        print(f"  Make sure the KME server is running:")
        print(f"    cd next-door-key-simulator")
        print(f"    python app.py")
        return 1
    
    # Cleanup before tests
    cleanup()
    
    # Run tests
    results = []
    results.append(("Registration", test_registration()))
    results.append(("Key Size", test_key_size()))
    results.append(("Cross-User Request", test_cross_user_key_request()))
    results.append(("Decryption Keys", test_decryption_keys()))
    results.append(("Pool Status", test_pool_status()))
    results.append(("Pool Refill", test_refill()))
    
    # Cleanup after tests
    cleanup()
    
    # Summary
    print_header("Summary")
    passed = sum(1 for _, r in results if r)
    failed = sum(1 for _, r in results if not r)
    
    print(f"  Total: {len(results)}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")
    
    for name, result in results:
        status = "✓" if result else "✗"
        print(f"    {status} {name}")
    
    if failed == 0:
        print("\n  ✓ ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n  ✗ {failed} TESTS FAILED")
        return 1


if __name__ == '__main__':
    sys.exit(main())
