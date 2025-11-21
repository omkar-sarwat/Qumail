import requests
import time

def test_post_kme_pool_replenish():
    KMS1_BASE = "http://127.0.0.1:9010"
    KMS2_BASE = "http://127.0.0.1:9020"
    timeout = 5
    enc_headers_kms1 = {
        "X-SAE-ID": "25840139-0dd4-49ae-ba1e-b86731601803",
        "X-Slave-SAE-ID": "c565d5aa-8670-4446-8471-b0e53e315d2a",
        "Connection": "close"
    }
    dec_headers_kms2 = {
        "X-SAE-ID": "c565d5aa-8670-4446-8471-b0e53e315d2a",
        "X-Slave-SAE-ID": "25840139-0dd4-49ae-ba1e-b86731601803",
        "Connection": "close"
    }
    kme_verify_headers = {"X-KMS-ID": "KMS-2", "Connection": "close"}

    replenish_url = f"{KMS2_BASE}/api/v1/kme/pool/replenish"
    enc_url = f"{KMS1_BASE}/api/v1/keys/enc_keys"
    verify_url = f"{KMS2_BASE}/api/v1/kme/verify"
    dec_url = f"{KMS2_BASE}/api/v1/keys/dec_keys"

    for _ in range(10):
        # Step 1: Request 2 encryption keys (size=256) from KMS-1
        enc_payload = {"number": 2, "size": 256}
        try:
            enc_resp = requests.post(enc_url, headers=enc_headers_kms1, json=enc_payload, timeout=timeout)
        except requests.exceptions.RequestException as e:
            raise AssertionError(f"KMS-1 encryption keys request failed: {e}")
        assert enc_resp.status_code == 200, f"KMS-1 /enc_keys POST returned {enc_resp.status_code}"
        try:
            enc_data = enc_resp.json()
        except Exception:
            raise AssertionError("KMS-1 /enc_keys response is not valid JSON")
        # Require keys or key_IDs to be present in response
        assert ("keys" in enc_data and isinstance(enc_data["keys"], list)) or ("key_IDs" in enc_data and isinstance(enc_data["key_IDs"], list)), "KMS-1 /enc_keys response missing keys or key_IDs list"

        # Extract key IDs for verification - try common key id fields
        key_ids = None
        if "key_IDs" in enc_data and isinstance(enc_data["key_IDs"], list):
            key_ids = enc_data["key_IDs"]
        elif "keys" in enc_data and isinstance(enc_data["keys"], list):
            # try to get id inside each key object
            key_ids = []
            for k in enc_data["keys"]:
                if isinstance(k, dict):
                    for possible_id_key in ["key_ID", "keyId", "id", "keyID"]:
                        if possible_id_key in k:
                            key_ids.append(str(k[possible_id_key]))
                            break
                else:
                    key_ids.append(str(k))
        else:
            key_ids = []
            for v in enc_data.values():
                if isinstance(v, list):
                    key_ids.extend(str(i) for i in v)
        if not key_ids or len(key_ids) < 2:
            raise AssertionError("Less than 2 key IDs received from /enc_keys")

        # Step 2: Verify on KMS-2 that keys are all_verified=true
        verify_payload = {"key_IDs": key_ids}
        try:
            verify_resp = requests.post(verify_url, headers=kme_verify_headers, json=verify_payload, timeout=timeout)
        except requests.exceptions.RequestException as e:
            raise AssertionError(f"KMS-2 /kme/verify request failed (KMS-2 may be unreachable): {e}")
        assert verify_resp.status_code == 200, f"KMS-2 /kme/verify returned {verify_resp.status_code}"
        try:
            verify_data = verify_resp.json()
        except Exception:
            raise AssertionError("KMS-2 /kme/verify response is not valid JSON")
        all_verified = verify_data.get("all_verified")
        assert all_verified is True, f"KMS-2 /kme/verify all_verified is not true (got {all_verified})"

        # Step 3: Request decryption keys for those key IDs from KMS-2 with swapped headers
        dec_payload = {"key_IDs": key_ids}
        try:
            dec_resp = requests.post(dec_url, headers=dec_headers_kms2, json=dec_payload, timeout=timeout)
        except requests.exceptions.RequestException as e:
            raise AssertionError(f"KMS-2 /dec_keys request failed: {e}")
        assert dec_resp.status_code == 200, f"KMS-2 /dec_keys POST returned {dec_resp.status_code}"
        try:
            dec_data = dec_resp.json()
        except Exception:
            raise AssertionError("KMS-2 /dec_keys response is not valid JSON")

        # We do not reuse keys so just confirm we get the requested keys back
        dec_key_ids_resp = None
        if "keys" in dec_data and isinstance(dec_data["keys"], list):
            dec_key_ids_resp = []
            for k in dec_data["keys"]:
                if isinstance(k, dict):
                    for possible_id_key in ["key_ID", "keyId", "id", "keyID"]:
                        if possible_id_key in k:
                            dec_key_ids_resp.append(str(k[possible_id_key]))
                            break
                else:
                    dec_key_ids_resp.append(str(k))
        elif "key_IDs" in dec_data and isinstance(dec_data["key_IDs"], list):
            dec_key_ids_resp = dec_data["key_IDs"]
        elif isinstance(dec_data, list):
            dec_key_ids_resp = [str(k) for k in dec_data]

        assert dec_key_ids_resp is not None, "Did not find key IDs in decryption keys response"
        assert set(dec_key_ids_resp) == set(key_ids), "Decryption keys returned do not match requested key IDs"
        # Small sleep to avoid socket buildup or rate limits
        time.sleep(0.1)

    # Step 4: Finally, call the KMS-2 /api/v1/kme/pool/replenish POST endpoint to trigger pool replenishment
    try:
        replenish_resp = requests.post(replenish_url, headers={"Connection": "close"}, timeout=timeout)
    except requests.exceptions.RequestException as e:
        raise AssertionError(f"KMS-2 /kme/pool/replenish request failed: {e}")
    assert replenish_resp.status_code == 200, f"/kme/pool/replenish returned {replenish_resp.status_code}"

test_post_kme_pool_replenish()
