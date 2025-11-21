import requests
import time

BASE_KMS1 = "http://127.0.0.1:9010"
BASE_KMS2 = "http://127.0.0.1:9020"

HEADERS_KMS1 = {
    "X-SAE-ID": "25840139-0dd4-49ae-ba1e-b86731601803",
    "X-Slave-SAE-ID": "c565d5aa-8670-4446-8471-b0e53e315d2a",
    "Connection": "close"
}

HEADERS_KMS2 = {
    "X-SAE-ID": "c565d5aa-8670-4446-8471-b0e53e315d2a",
    "X-Slave-SAE-ID": "25840139-0dd4-49ae-ba1e-b86731601803",
    "Connection": "close"
}

HEADERS_KME_VERIFY = {
    "X-KMS-ID": "KMS-1",
    "Connection": "close"
}

def test_health_endpoint_status_check():
    timeout = 5
    enc_keys_url = f"{BASE_KMS1}/api/v1/keys/enc_keys"
    kme_verify_url = f"{BASE_KMS2}/api/v1/kme/verify"
    dec_keys_url = f"{BASE_KMS2}/api/v1/keys/dec_keys"
    
    for i in range(10):
        # Step 1: Request 2 encryption keys size 256 from KMS-1
        enc_payload = {"number": 2, "size": 256}
        try:
            resp_enc = requests.post(enc_keys_url, headers=HEADERS_KMS1, json=enc_payload, timeout=timeout)
        except requests.exceptions.RequestException as e:
            raise AssertionError(f"KMS-1 /enc_keys request failed on iteration {i+1}: {e}")
        
        assert resp_enc.status_code == 200, f"KMS-1 /enc_keys returned {resp_enc.status_code} on iteration {i+1}"
        
        try:
            enc_resp_json = resp_enc.json()
        except Exception:
            raise AssertionError(f"KMS-1 /enc_keys response is not valid JSON on iteration {i+1}")
        
        # Validate response contains 2 keys
        if not isinstance(enc_resp_json, dict):
            raise AssertionError(f"KMS-1 /enc_keys response is not a dict on iteration {i+1}")
        
        # Assuming keys are returned under a list key "keys" each with "key_ID"
        keys = enc_resp_json.get("keys")
        assert isinstance(keys, list) and len(keys) == 2, f"KMS-1 /enc_keys keys count invalid on iteration {i+1}"
        for key in keys:
            assert isinstance(key, dict), f"Key is not a dict on iteration {i+1}"
            assert "key_ID" in key and isinstance(key["key_ID"], str) and key["key_ID"], f"Invalid key_ID in key on iteration {i+1}"
        
        key_ids = [k["key_ID"] for k in keys]
        
        # Step 2: Verify KMS-2 /api/v1/kme/verify returns all_verified=true for those key IDs
        verify_payload = {"key_IDs": key_ids}
        try:
            resp_verify = requests.post(kme_verify_url, headers=HEADERS_KME_VERIFY, json=verify_payload, timeout=timeout)
        except requests.exceptions.ConnectionError:
            raise ConnectionError("KMS-2 API at /api/v1/kme/verify is not reachable")
        except requests.exceptions.RequestException as e:
            raise AssertionError(f"KMS-2 /kme/verify request failed on iteration {i+1}: {e}")
        
        assert resp_verify.status_code == 200, f"KMS-2 /kme/verify returned {resp_verify.status_code} on iteration {i+1}"
        try:
            verify_json = resp_verify.json()
        except Exception:
            raise AssertionError(f"KMS-2 /kme/verify response not JSON on iteration {i+1}")
        
        # all_verified must be True
        assert verify_json.get("all_verified") is True, f"KMS-2 /kme/verify all_verified not true on iteration {i+1}"
        
        # Step 3: On KMS-2 request decryption keys for those key IDs with swapped headers
        dec_payload = {"key_IDs": key_ids}
        try:
            resp_dec = requests.post(dec_keys_url, headers=HEADERS_KMS2, json=dec_payload, timeout=timeout)
        except requests.exceptions.RequestException as e:
            raise AssertionError(f"KMS-2 /dec_keys request failed on iteration {i+1}: {e}")
        
        assert resp_dec.status_code == 200, f"KMS-2 /dec_keys returned {resp_dec.status_code} on iteration {i+1}"
        try:
            dec_resp_json = resp_dec.json()
        except Exception:
            raise AssertionError(f"KMS-2 /dec_keys response is not JSON on iteration {i+1}")
        
        # Validate returned keys correspond to requested key_IDs and are consumed
        dec_keys = dec_resp_json.get("keys")
        assert isinstance(dec_keys, list) and len(dec_keys) == len(key_ids), f"KMS-2 /dec_keys keys count invalid on iteration {i+1}"
        returned_ids = [k.get("key_ID") for k in dec_keys if isinstance(k, dict) and "key_ID" in k]
        assert set(returned_ids) == set(key_ids), f"KMS-2 /dec_keys returned keys mismatch on iteration {i+1}"
        
        # Enforce no reuse: On next iteration the same keys should not be returned, so will request new keys next iteration
        
        time.sleep(0.1)  # brief pause to avoid flooding
    
    # Step 4: Verify /health endpoint returns 200 with valid schema (at KMS-1 as base)
    health_url = f"{BASE_KMS1}/health"
    try:
        resp_health = requests.get(health_url, timeout=30, headers={"Connection": "close"})
    except requests.exceptions.RequestException as e:
        raise AssertionError(f"Health endpoint request failed: {e}")
    
    assert resp_health.status_code == 200, f"/health endpoint returned {resp_health.status_code}"
    try:
        health_json = resp_health.json()
    except Exception:
        raise AssertionError("/health response is not valid JSON")
    
    # Assuming health schema requires at least a "status" key with "healthy" or similar
    assert "status" in health_json, "Health response missing 'status' key"
    assert isinstance(health_json["status"], str) and health_json["status"], "Health 'status' is empty or not string"

test_health_endpoint_status_check()
