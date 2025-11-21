import requests
import time

BASE_KMS_1 = "http://127.0.0.1:9010"
BASE_KMS_2 = "http://127.0.0.1:9020"
TIMEOUT = 5

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

X_KMS_ID_KMS_1 = "KMS-1"
X_KMS_ID_KMS_2 = "KMS-2"


def test_post_kme_sync_receive_keys_for_synchronization():
    for i in range(10):
        # Step 1: On KMS-1 call /api/v1/keys/enc_keys with 2 keys of size 256
        enc_keys_payload = {"number": 2, "size": 256}
        try:
            r_enc = requests.post(
                f"{BASE_KMS_1}/api/v1/keys/enc_keys",
                headers=HEADERS_KMS_1,
                json=enc_keys_payload,
                timeout=TIMEOUT,
                )
            r_enc.raise_for_status()
        except requests.exceptions.RequestException as e:
            assert False, f"KMS-1 /enc_keys request failed at iteration {i+1}: {e}"
        enc_keys_data = r_enc.json()
        # Expecting keys returned as a list or dict containing keys with IDs
        # We try to extract key_IDs for verification and dec_keys request
        # Assume response structure includes a list of keys with an 'ID' or 'key_ID' field.
        # We'll check multiple common possible structures.
        key_ids = []
        if isinstance(enc_keys_data, dict):
            keys = enc_keys_data.get("keys")
            if keys and isinstance(keys, list):
                for key in keys:
                    if "ID" in key:
                        key_ids.append(key["ID"])
                    elif "key_ID" in key:
                        key_ids.append(key["key_ID"])
                    elif "KeyID" in key:
                        key_ids.append(key["KeyID"])
            elif isinstance(enc_keys_data.get("data"), list):
                for key in enc_keys_data.get("data"):
                    if "ID" in key:
                        key_ids.append(key["ID"])
            elif isinstance(enc_keys_data, list):
                for key in enc_keys_data:
                    if isinstance(key, dict):
                        if "ID" in key:
                            key_ids.append(key["ID"])
        elif isinstance(enc_keys_data, list):
            for key in enc_keys_data:
                if isinstance(key, dict) and "ID" in key:
                    key_ids.append(key["ID"])

        assert len(key_ids) >= 2, f"Expected at least 2 keys from enc_keys, got {len(key_ids)} at iteration {i+1}"

        # Step 2: Verify KMS-2 /api/v1/kme/verify returns all_verified=true for those key IDs
        verify_headers = {"X-KMS-ID": X_KMS_ID_KMS_2, "Connection": "close"}
        try:
            r_verify = requests.post(
                f"{BASE_KMS_2}/api/v1/kme/verify",
                headers=verify_headers,
                timeout=TIMEOUT,
            )
            r_verify.raise_for_status()
        except requests.exceptions.RequestException as e:
            assert False, f"KMS-2 /kme/verify request failed at iteration {i+1}: {e}"
        verify_data = r_verify.json()
        # Validate all_verified = true in response
        assert (
            isinstance(verify_data, dict)
            and verify_data.get("all_verified") is True
        ), f"/kme/verify did not return all_verified=true at iteration {i+1}: {verify_data}"

        # Step 3: On KMS-2 call /api/v1/keys/dec_keys for those key IDs with swapped headers
        dec_keys_payload = {"key_IDs": key_ids}
        try:
            r_dec = requests.post(
                f"{BASE_KMS_2}/api/v1/keys/dec_keys",
                headers=HEADERS_KMS_2,
                json=dec_keys_payload,
                timeout=TIMEOUT,
            )
            r_dec.raise_for_status()
        except requests.exceptions.RequestException as e:
            assert False, f"KMS-2 /dec_keys request failed at iteration {i+1}: {e}"
        dec_keys_data = r_dec.json()
        dec_key_ids = []
        if isinstance(dec_keys_data, dict):
            keys = dec_keys_data.get("keys")
            if keys and isinstance(keys, list):
                for key in keys:
                    if "ID" in key:
                        dec_key_ids.append(key["ID"])
                    elif "key_ID" in key:
                        dec_key_ids.append(key["key_ID"])
                    elif "KeyID" in key:
                        dec_key_ids.append(key["KeyID"])
            elif isinstance(dec_keys_data.get("data"), list):
                for key in dec_keys_data.get("data"):
                    if "ID" in key:
                        dec_key_ids.append(key["ID"])
            elif isinstance(dec_keys_data, list):
                for key in dec_keys_data:
                    if isinstance(key, dict):
                        if "ID" in key:
                            dec_key_ids.append(key["ID"])
        elif isinstance(dec_keys_data, list):
            for key in dec_keys_data:
                if isinstance(key, dict) and "ID" in key:
                    dec_key_ids.append(key["ID"])

        assert set(key_ids).issubset(set(dec_key_ids)), f"Returned dec_keys do not include all requested keys at iteration {i+1}"

        # Step 4: On KMS-1 call /api/v1/kme/sync with keys from enc_keys to simulate sync
        sync_payload = {"keys": enc_keys_data.get("keys") if isinstance(enc_keys_data, dict) else enc_keys_data}
        if not sync_payload["keys"]:
            sync_payload = {"keys": enc_keys_data}

        sync_headers = {"X-KMS-ID": X_KMS_ID_KMS_2, "Connection": "close"}

        try:
            r_sync = requests.post(
                f"{BASE_KMS_1}/api/v1/kme/sync",
                headers=sync_headers,
                json=sync_payload,
                timeout=TIMEOUT,
            )
            r_sync.raise_for_status()
        except requests.exceptions.RequestException as e:
            assert False, f"KMS-1 /kme/sync request failed at iteration {i+1}: {e}"
        assert r_sync.status_code == 200, f"/kme/sync did not return 200 OK at iteration {i+1}"

        time.sleep(0.1)


test_post_kme_sync_receive_keys_for_synchronization()