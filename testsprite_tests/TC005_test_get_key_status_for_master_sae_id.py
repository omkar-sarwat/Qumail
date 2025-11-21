import requests
import time

def test_get_key_status_for_master_sae_id():
    kms1_base = "http://127.0.0.1:9010"
    kms2_base = "http://127.0.0.1:9020"
    timeout = 5
    master_sae_id = "25840139-0dd4-49ae-ba1e-b86731601803"
    slave_sae_id = "c565d5aa-8670-4446-8471-b0e53e315d2a"
    headers_kms1_enc = {
        "X-SAE-ID": master_sae_id,
        "X-Slave-SAE-ID": slave_sae_id,
        "Connection": "close"
    }
    headers_kms2_kme = {
        "X-KMS-ID": "KMS-1",
        "Connection": "close"
    }
    headers_kms2_dec = {
        "X-SAE-ID": slave_sae_id,
        "X-Slave-SAE-ID": master_sae_id,
        "Connection": "close"
    }

    enc_keys_url = f"{kms1_base}/api/v1/keys/enc_keys"
    kme_verify_url = f"{kms2_base}/api/v1/kme/verify"
    dec_keys_url = f"{kms2_base}/api/v1/keys/dec_keys"
    key_status_url = f"{kms1_base}/api/v1/keys/{master_sae_id}/status"

    for _ in range(10):
        try:
            # Step 1: On KMS-1 call /api/v1/keys/enc_keys to get 2 keys size 256
            payload_enc = {"number": 2, "size": 256}
            resp_enc = requests.post(enc_keys_url, headers=headers_kms1_enc, json=payload_enc, timeout=timeout)
            assert resp_enc.status_code == 200, f"KMS-1 enc_keys failed with status {resp_enc.status_code}"
            resp_enc_json = resp_enc.json()
            assert isinstance(resp_enc_json, dict), "Response for enc_keys is not a JSON object"
            keys = resp_enc_json.get("keys")
            assert keys is not None and isinstance(keys, list), "Response missing 'keys' list"
            assert len(keys) == 2, f"Expected 2 keys, got {len(keys)}"
            key_ids = [k.get("key_ID") for k in keys]
            for kid in key_ids:
                assert isinstance(kid, str) and kid, "Invalid or missing key_ID"
            for k in keys:
                size = k.get("size")
                assert size == 256, f"Key size expected 256, got {size}"

            # Step 2: Verify all keys on KMS-2 /api/v1/kme/verify returns all_verified=true
            verify_payload = {"key_IDs": key_ids}
            headers_kms2_kme["Connection"] = "close"
            resp_verify = requests.post(kme_verify_url, headers=headers_kms2_kme, json=verify_payload, timeout=timeout)
            if resp_verify.status_code == 404 or resp_verify.status_code >= 500:
                raise ConnectionError("KMS-2 verification endpoint not reachable or error")
            assert resp_verify.status_code == 200, f"KMS-2 kme/verify failed with status {resp_verify.status_code}"
            resp_verify_json = resp_verify.json()
            all_verified = resp_verify_json.get("all_verified")
            assert all_verified is True, "Keys not all verified on KMS-2"

            # Step 3: On KMS-2 call /api/v1/keys/dec_keys for those key_IDs with headers swapped
            payload_dec = {"key_IDs": key_ids}
            resp_dec = requests.post(dec_keys_url, headers=headers_kms2_dec, json=payload_dec, timeout=timeout)
            assert resp_dec.status_code == 200, f"KMS-2 dec_keys failed with status {resp_dec.status_code}"
            resp_dec_json = resp_dec.json()
            dec_keys = resp_dec_json.get("keys")
            assert isinstance(dec_keys, list), "dec_keys response missing 'keys' list"
            dec_key_ids = [k.get("key_ID") for k in dec_keys]
            assert set(dec_key_ids) == set(key_ids), "Mismatch between requested and returned decryption key IDs"

            # Step 4: Verify /api/v1/keys/{master_sae_id}/status returns correct counts and size limits
            resp_status = requests.get(key_status_url, headers={"X-Slave-SAE-ID": slave_sae_id, "Connection": "close"}, timeout=timeout)
            assert resp_status.status_code == 200, f"Key status endpoint failed with status {resp_status.status_code}"
            status_json = resp_status.json()
            stored_keys_count = status_json.get("stored_keys_count")
            size_limit = status_json.get("size_limit")
            # As keys are consumed after dec_keys call, stored_keys_count might be 0 or decreasing but size_limit should be 256 or consistent
            assert stored_keys_count is not None and isinstance(stored_keys_count, int), "stored_keys_count missing or invalid"
            assert size_limit is not None and isinstance(size_limit, int), "size_limit missing or invalid"
            # We expect size_limit to be at least 256 (per key size used)
            assert size_limit >= 256, f"size_limit expected >=256, got {size_limit}"

        except requests.ConnectionError:
            raise RuntimeError("KMS-2 service is not reachable at http://127.0.0.1:9020")
        except Exception:
            raise
        time.sleep(0.2)  # small delay between iterations to avoid rate limiting

test_get_key_status_for_master_sae_id()
