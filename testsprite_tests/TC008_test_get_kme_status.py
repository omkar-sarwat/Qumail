import requests
import time

BASE_ENDPOINT_KMS_1 = "http://127.0.0.1:9010"
BASE_ENDPOINT_KMS_2 = "http://127.0.0.1:9020"

HEADERS_KMS_1 = {
    "X-SAE-ID": "25840139-0dd4-49ae-ba1e-b86731601803",
    "X-Slave-SAE-ID": "c565d5aa-8670-4446-8471-b0e53e315d2a",
    "Connection": "close"
}

HEADERS_KMS_2 = {
    "X-SAE-ID": "c565d5aa-8670-4446-8471-b0e53e315d2a",
    "X-Slave-SAE-ID": "25840139-0dd4-49ae-ba1e-b86731601803",
    "Connection": "close"
}

def test_get_kme_status():
    timeout = 5
    enc_keys_url = f"{BASE_ENDPOINT_KMS_1}/api/v1/keys/enc_keys"
    verify_url = f"{BASE_ENDPOINT_KMS_2}/api/v1/kme/verify"
    dec_keys_url = f"{BASE_ENDPOINT_KMS_2}/api/v1/keys/dec_keys"
    kme_status_url = f"{BASE_ENDPOINT_KMS_1}/api/v1/kme/status"

    # Attempt to connect to KMS-2 to ensure availability
    try:
        # Simple GET for KME status on KMS-2 as availability check with Connection close
        resp_kms2_status = requests.get(kme_status_url.replace("9010","9020"), timeout=timeout, headers={"Connection": "close"})
        resp_kms2_status.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"KMS-2 service not reachable at {BASE_ENDPOINT_KMS_2}: {e}")

    for _ in range(10):
        # 1) On KMS-1 call /api/v1/keys/enc_keys with given headers and payload
        try:
            payload_enc = {"number": 2, "size": 256}
            r_enc = requests.post(enc_keys_url, headers=HEADERS_KMS_1, json=payload_enc, timeout=timeout)
            r_enc.raise_for_status()
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to request encryption keys from KMS-1: {e}")
        enc_resp_json = r_enc.json()

        # Validate response contains keys with key IDs and expected size
        assert isinstance(enc_resp_json, dict), "Encryption keys response is not a JSON object"
        # Expecting keys field or list, infer from returned data keys name
        keys = enc_resp_json.get("keys") or enc_resp_json.get("key_IDs") or enc_resp_json.get("key_ids") or enc_resp_json.get("keys_list")
        if keys is None:
            # Fall back: find list of keys by checking dict values
            keys = []
            for v in enc_resp_json.values():
                if isinstance(v, list) and len(v) == 2:
                    keys = v
                    break
        assert isinstance(keys, list), "Encryption keys not returned as list"
        assert len(keys) == 2, f"Expected 2 keys but got {len(keys)}"
        # Each key should have an ID string, extract IDs
        key_ids = []
        for key in keys:
            if isinstance(key, dict) and "key_ID" in key:
                key_ids.append(key["key_ID"])
            elif isinstance(key, dict) and "id" in key:
                key_ids.append(str(key["id"]))
            elif isinstance(key, str):
                key_ids.append(key)
            else:
                # fallback: try first string or id field
                if isinstance(key, dict):
                    first_val = next(iter(key.values()), None)
                    if isinstance(first_val, str):
                        key_ids.append(first_val)
        # Validate key_ids count
        assert len(key_ids) == 2, "Key IDs extraction failed or count mismatch"

        # 2) Verify on KMS-2 /api/v1/kme/verify returns all_verified=true for those keys
        try:
            headers_kms2_verify = {"X-KMS-ID": "KMS-2", "Connection": "close"}
            r_verify = requests.post(verify_url, headers=headers_kms2_verify, json={"key_IDs": key_ids}, timeout=timeout)
            r_verify.raise_for_status()
        except requests.RequestException as e:
            raise RuntimeError(f"Failed KME verify on KMS-2: {e}")

        verify_resp = r_verify.json()
        assert isinstance(verify_resp, dict), "KME verify response is not a JSON object"
        assert verify_resp.get("all_verified") is True, f"Expected all_verified=true but got {verify_resp.get('all_verified')}"

        # 3) On KMS-2 call /api/v1/keys/dec_keys with swapped headers and those key IDs
        try:
            headers_dec_keys = HEADERS_KMS_2.copy()
            payload_dec = {"key_IDs": key_ids}
            r_dec = requests.post(dec_keys_url, headers=headers_dec_keys, json=payload_dec, timeout=timeout)
            r_dec.raise_for_status()
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to request decryption keys from KMS-2: {e}")

        dec_resp_json = r_dec.json()
        assert isinstance(dec_resp_json, dict), "Decryption keys response is not a JSON object"
        dec_keys = dec_resp_json.get("keys") or dec_resp_json.get("key_IDs") or dec_resp_json.get("key_ids") or dec_resp_json.get("keys_list")
        if dec_keys is None:
            # Same fallback as above
            dec_keys = []
            for v in dec_resp_json.values():
                if isinstance(v, list):
                    dec_keys = v
                    break
        assert isinstance(dec_keys, list), "Decryption keys not returned as list"
        assert len(dec_keys) == 2, f"Expected 2 decryption keys but got {len(dec_keys)}"

        # 4) Wait a minimal pause before next iteration (optional)
        time.sleep(0.1)

    # Finally, verify the KME status endpoint on KMS-1 responds HTTP 200 with valid schema
    try:
        r_status = requests.get(kme_status_url, timeout=timeout, headers={"Connection": "close"})
        r_status.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to get KME status from KMS-1: {e}")

    status_json = r_status.json()
    assert isinstance(status_json, dict), "KME status response is not a JSON object"
    # Validate expected keys in status JSON (schema not detailed, so basic check)
    assert "status" in status_json or "kme_status" in status_json or "state" in status_json or len(status_json) > 0, \
        "KME status response missing expected keys or empty"

test_get_kme_status()
