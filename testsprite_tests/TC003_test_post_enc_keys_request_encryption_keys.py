import requests
import time

BASE_KMS1 = "http://127.0.0.1:9010"
BASE_KMS2 = "http://127.0.0.1:9020"
TIMEOUT = 5

X_SAE_ID_KMS1 = "25840139-0dd4-49ae-ba1e-b86731601803"
X_SLAVE_SAE_ID_KMS1 = "c565d5aa-8670-4446-8471-b0e53e315d2a"

X_SAE_ID_KMS2 = X_SLAVE_SAE_ID_KMS1
X_SLAVE_SAE_ID_KMS2 = X_SAE_ID_KMS1

HEADERS_KMS1 = {
    "X-SAE-ID": X_SAE_ID_KMS1,
    "X-Slave-SAE-ID": X_SLAVE_SAE_ID_KMS1,
    "Connection": "close"
}

HEADERS_KMS2_VERIFY = {
    "X-KMS-ID": "KMS-1",
    "Connection": "close"
}

HEADERS_KMS2_DEC_KEYS = {
    "X-SAE-ID": X_SAE_ID_KMS2,
    "X-Slave-SAE-ID": X_SLAVE_SAE_ID_KMS2,
    "Connection": "close"
}

def test_post_enc_keys_request_encryption_keys():
    for i in range(10):
        # Step 1: On KMS-1 call /api/v1/keys/enc_keys
        url_enc_keys = f"{BASE_KMS1}/api/v1/keys/enc_keys"
        payload_enc = {"number": 2, "size": 256}

        start_time = time.time()
        try:
            resp_enc = requests.post(url_enc_keys, headers=HEADERS_KMS1, json=payload_enc, timeout=TIMEOUT)
        except requests.exceptions.RequestException as e:
            raise AssertionError(f"KMS-1 /enc_keys request failed on iteration {i+1}: {e}")
        elapsed_enc = time.time() - start_time

        assert resp_enc.status_code == 200, f"KMS-1 /enc_keys returned status {resp_enc.status_code}, iteration {i+1}"
        assert elapsed_enc <= 2, f"KMS-1 /enc_keys response time {elapsed_enc:.2f}s exceeded 2s, iteration {i+1}"

        try:
            data_enc = resp_enc.json()
        except ValueError:
            raise AssertionError(f"KMS-1 /enc_keys returned invalid JSON, iteration {i+1}")

        # Validate that keys returned and extract key IDs
        keys = data_enc.get("keys") or data_enc.get("key_IDs") or data_enc.get("key_ids")
        if keys is None:
            # If no "keys" field, fallback try keys list with subfields
            keys = []
            if isinstance(data_enc, dict):
                # try to detect keys in data_enc values
                for v in data_enc.values():
                    if isinstance(v, list):
                        keys = v
                        break
        assert isinstance(keys, list), f"KMS-1 /enc_keys response keys field missing or not list, iteration {i+1}"
        assert len(keys) == 2, f"KMS-1 /enc_keys returned {len(keys)} keys, expected 2, iteration {i+1}"

        key_ids = []
        # If keys are dict with id fields
        for k in keys:
            if isinstance(k, dict):
                kid = k.get("key_ID") or k.get("key_id") or k.get("id")
                if kid:
                    key_ids.append(kid)
            elif isinstance(k, str):
                key_ids.append(k)
        assert len(key_ids) == 2, f"Failed to extract 2 key IDs from keys response, iteration {i+1}"

        # Step 2: Verify KMS-2 /api/v1/kme/verify returns all_verified=true
        url_verify = f"{BASE_KMS2}/api/v1/kme/verify"
        payload_verify = {"key_IDs": key_ids}

        try:
            resp_verify = requests.post(url_verify, headers=HEADERS_KMS2_VERIFY, json=payload_verify, timeout=TIMEOUT)
        except requests.exceptions.RequestException as e:
            raise AssertionError(f"KMS-2 /kme/verify request failed on iteration {i+1} (KMS-2 might be unreachable): {e}")

        assert resp_verify.status_code == 200, f"KMS-2 /kme/verify returned status {resp_verify.status_code}, iteration {i+1}"

        try:
            data_verify = resp_verify.json()
        except ValueError:
            raise AssertionError(f"KMS-2 /kme/verify returned invalid JSON, iteration {i+1}")

        all_verified = data_verify.get("all_verified")
        assert all_verified is True, f"KMS-2 /kme/verify all_verified!=True, iteration {i+1}"

        # Step 3: On KMS-2 call /api/v1/keys/dec_keys for those key IDs with headers swapped
        url_dec_keys = f"{BASE_KMS2}/api/v1/keys/dec_keys"
        payload_dec = {"key_IDs": key_ids}

        start_time_dec = time.time()
        try:
            resp_dec = requests.post(url_dec_keys, headers=HEADERS_KMS2_DEC_KEYS, json=payload_dec, timeout=TIMEOUT)
        except requests.exceptions.RequestException as e:
            raise AssertionError(f"KMS-2 /dec_keys request failed on iteration {i+1}: {e}")
        elapsed_dec = time.time() - start_time_dec

        assert resp_dec.status_code == 200, f"KMS-2 /dec_keys returned status {resp_dec.status_code}, iteration {i+1}"
        assert elapsed_dec <= 2, f"KMS-2 /dec_keys response time {elapsed_dec:.2f}s exceeded 2s, iteration {i+1}"

        try:
            data_dec = resp_dec.json()
        except ValueError:
            raise AssertionError(f"KMS-2 /dec_keys returned invalid JSON, iteration {i+1}")

        # Verify returned keys for consumption
        keys_dec = data_dec.get("keys") or data_dec.get("key_IDs") or data_dec.get("key_ids")
        assert isinstance(keys_dec, list), f"KMS-2 /dec_keys keys field missing or not list, iteration {i+1}"
        assert len(keys_dec) == 2, f"KMS-2 /dec_keys returned {len(keys_dec)} keys, expected 2, iteration {i+1}"

    print("test_post_enc_keys_request_encryption_keys passed 10 sequential iterations.")

test_post_enc_keys_request_encryption_keys()