import requests
from requests.exceptions import RequestException

BASE_KMS1 = "http://127.0.0.1:9010"
BASE_KMS2 = "http://127.0.0.1:9020"


def test_post_kme_verify_keys_exist():
    timeout = 5
    enc_keys_url = f"{BASE_KMS1}/api/v1/keys/enc_keys"
    verify_url = f"{BASE_KMS2}/api/v1/kme/verify"
    dec_keys_url = f"{BASE_KMS2}/api/v1/keys/dec_keys"

    headers_kms1 = {
        "X-SAE-ID": "25840139-0dd4-49ae-ba1e-b86731601803",
        "X-Slave-SAE-ID": "c565d5aa-8670-4446-8471-b0e53e315d2a",
        "Connection": "close"
    }
    headers_kms2_verify = {
        "X-KMS-ID": "KMS-1",
        "Connection": "close"
    }
    headers_kms2_dec = {
        "X-SAE-ID": "c565d5aa-8670-4446-8471-b0e53e315d2a",
        "X-Slave-SAE-ID": "25840139-0dd4-49ae-ba1e-b86731601803",
        "Connection": "close"
    }

    for _ in range(10):
        try:
            # Step 1: Request encryption keys from KMS-1
            enc_req_payload = {"number": 2, "size": 256}
            try:
                enc_resp = requests.post(enc_keys_url, headers=headers_kms1, json=enc_req_payload, timeout=timeout)
            except RequestException as e:
                raise RuntimeError(f"KMS-1 /api/v1/keys/enc_keys endpoint not reachable or failed: {e}")
            assert enc_resp.status_code == 200, f"Expected 200 from KMS-1 enc_keys, got {enc_resp.status_code}"
            enc_resp_json = enc_resp.json()
            assert isinstance(enc_resp_json, dict), "KMS-1 enc_keys response is not a JSON object"
            assert "keys" in enc_resp_json or "key_IDs" in enc_resp_json, "No keys or key_IDs in KMS-1 response"
            
            # Extract key IDs for verification
            # The response schema is not explicitly defined for keys key names,
            # we assume keys are under "keys" or "key_IDs" as a list of dicts or strings.
            if "keys" in enc_resp_json:
                # keys is list of dicts, each having "key_ID" or "id"
                keys_list = enc_resp_json["keys"]
                if keys_list and isinstance(keys_list, list):
                    key_ids = []
                    for k in keys_list:
                        if isinstance(k, dict):
                            if "key_ID" in k:
                                key_ids.append(k["key_ID"])
                            elif "id" in k:
                                key_ids.append(k["id"])
                            else:
                                raise AssertionError("Key object missing key_ID or id")
                        elif isinstance(k, str):
                            key_ids.append(k)
                    assert len(key_ids) == 2, f"Expected 2 keys, got {len(key_ids)}"
                else:
                    raise AssertionError("keys field is not a list with expected keys")
            elif "key_IDs" in enc_resp_json:
                key_ids = enc_resp_json["key_IDs"]
                assert isinstance(key_ids, list), "key_IDs is not a list"
                assert len(key_ids) == 2, f"Expected 2 key_IDs, got {len(key_ids)}"
            else:
                raise AssertionError("No valid keys or key_IDs found in response")

            # Step 2: Verify keys exist on KMS-2 using /api/v1/kme/verify
            verify_payload = {"key_IDs": key_ids}
            try:
                verify_resp = requests.post(verify_url, headers=headers_kms2_verify, json=verify_payload, timeout=timeout)
            except RequestException as e:
                raise RuntimeError(f"KMS-2 /api/v1/kme/verify endpoint not reachable or failed: {e}")
            assert verify_resp.status_code == 200, f"Expected 200 from KMS-2 kme/verify, got {verify_resp.status_code}"

            verify_resp_json = verify_resp.json()
            assert isinstance(verify_resp_json, dict), "KMS-2 kme/verify response is not a JSON object"
            assert verify_resp_json.get("all_verified") is True, f"Expected all_verified=True, got {verify_resp_json.get('all_verified')}"

            # Step 3: Request decryption keys from KMS-2 for those key IDs with headers swapped
            dec_req_payload = {"key_IDs": key_ids}
            try:
                dec_resp = requests.post(dec_keys_url, headers=headers_kms2_dec, json=dec_req_payload, timeout=timeout)
            except RequestException as e:
                raise RuntimeError(f"KMS-2 /api/v1/keys/dec_keys endpoint not reachable or failed: {e}")
            assert dec_resp.status_code == 200, f"Expected 200 from KMS-2 dec_keys, got {dec_resp.status_code}"
            dec_resp_json = dec_resp.json()
            assert isinstance(dec_resp_json, dict), "KMS-2 dec_keys response is not a JSON object"
            # expect keys or similar in response
            keys_returned = dec_resp_json.get("keys") or dec_resp_json.get("key_IDs") or dec_resp_json.get("decrypted_keys")
            assert keys_returned is not None, "No keys returned by KMS-2 dec_keys"
            if isinstance(keys_returned, list):
                # Should match requested keys and length 2
                assert len(keys_returned) == 2, f"Expected 2 keys in dec_keys response, got {len(keys_returned)}"
            else:
                raise AssertionError("Keys returned by dec_keys is not a list")

        except AssertionError as ae:
            raise AssertionError(f"Assertion failed during iteration: {ae}")

        except RuntimeError as re:
            raise RuntimeError(str(re))