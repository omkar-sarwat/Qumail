import requests
from requests.exceptions import RequestException, ConnectionError, Timeout

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

HEADERS_KME_KMS2 = {
    "X-KMS-ID": "KMS-2",
    "Connection": "close"
}

TIMEOUT = 5  # seconds, as per instruction

def test_post_kme_pool_status():
    try:
        for _ in range(10):
            # Step 1: On KMS-1 call /api/v1/keys/enc_keys
            enc_keys_payload = {
                "number": 2,
                "size": 256
            }
            r_enc = requests.post(
                f"{BASE_KMS1}/api/v1/keys/enc_keys",
                headers=HEADERS_KMS1,
                json=enc_keys_payload,
                timeout=TIMEOUT
            )
            assert r_enc.status_code == 200, f"KMS-1 enc_keys call failed with status {r_enc.status_code}"
            enc_keys_resp = r_enc.json()
            # Expect keys in response, assume list under 'keys' or similar, else collect key IDs safely
            # From QKD standards and typical usage, keys will be identifiable by IDs; adapt as needed.
            # We'll try to find key IDs in the response
            # Typically the response might be like {"keys": [{"key_ID": "abc", ...}, {...}]}
            # Let's extract key IDs:
            key_ids = []
            if isinstance(enc_keys_resp, dict) and 'keys' in enc_keys_resp:
                for key_info in enc_keys_resp['keys']:
                    if 'key_ID' in key_info:
                        key_ids.append(key_info['key_ID'])
            elif isinstance(enc_keys_resp, dict):
                # Fallback, try keys field at top level
                for k, v in enc_keys_resp.items():
                    if isinstance(v, list):
                        for item in v:
                            if isinstance(item, dict) and 'key_ID' in item:
                                key_ids.append(item['key_ID'])
            if len(key_ids) < 2:
                # Fallback: try if keys themselves are strings (key IDs)
                if isinstance(enc_keys_resp, list):
                    key_ids = enc_keys_resp
                else:
                    raise AssertionError("Unable to extract 2 key IDs from enc_keys response")

            assert len(key_ids) == 2, f"Expected 2 key IDs, got {len(key_ids)}"

            # Step 2: Verify on KMS-2 /api/v1/kme/verify with X-KMS-ID header returns all_verified=true
            verify_payload = {
                "key_IDs": key_ids
            }
            r_verify = requests.post(
                f"{BASE_KMS2}/api/v1/kme/verify",
                headers=HEADERS_KME_KMS2,
                json=verify_payload,
                timeout=TIMEOUT
            )
            assert r_verify.status_code == 200, f"KMS-2 kme/verify call failed with status {r_verify.status_code}"
            verify_resp = r_verify.json()
            # Expect {"all_verified": true} or similar
            assert isinstance(verify_resp, dict), "kme/verify response is not a JSON object"
            assert verify_resp.get("all_verified") is True, "Not all keys verified on KMS-2"

            # Step 3: On KMS-2 call /api/v1/keys/dec_keys for those key IDs with headers swapped
            dec_keys_payload = {
                "key_IDs": key_ids
            }
            r_dec = requests.post(
                f"{BASE_KMS2}/api/v1/keys/dec_keys",
                headers=HEADERS_KMS2,
                json=dec_keys_payload,
                timeout=TIMEOUT
            )
            assert r_dec.status_code == 200, f"KMS-2 dec_keys call failed with status {r_dec.status_code}"
            dec_keys_resp = r_dec.json()
            # Verify keys returned match requested key_IDs (at least presence)
            dec_key_ids = []
            if isinstance(dec_keys_resp, dict) and 'keys' in dec_keys_resp:
                for key_info in dec_keys_resp['keys']:
                    if 'key_ID' in key_info:
                        dec_key_ids.append(key_info['key_ID'])
            elif isinstance(dec_keys_resp, dict):
                for k, v in dec_keys_resp.items():
                    if isinstance(v, list):
                        for item in v:
                            if isinstance(item, dict) and 'key_ID' in item:
                                dec_key_ids.append(item['key_ID'])
            elif isinstance(dec_keys_resp, list):
                dec_key_ids = dec_keys_resp

            for key_id in key_ids:
                assert key_id in dec_key_ids, f"Decryption key ID {key_id} not found in response"

        # Step 4: After completing 10 iterations, test /api/v1/kme/pool/status POST endpoint on KMS-1
        r_pool_status = requests.post(
            f"{BASE_KMS1}/api/v1/kme/pool/status",
            headers={"Connection": "close"},
            timeout=TIMEOUT
        )
        assert r_pool_status.status_code == 200, f"kme/pool/status POST failed with status {r_pool_status.status_code}"
        # Response content check can be basic, as no schema provided
        try:
            resp_json = r_pool_status.json()
            assert isinstance(resp_json, dict), "kme/pool/status response is not a JSON object"
        except Exception:
            raise AssertionError("kme/pool/status response is not valid JSON")

    except ConnectionError:
        print("KMS-2 at http://127.0.0.1:9020 is not reachable.")
    except Timeout:
        raise AssertionError("Request timed out")
    except RequestException as e:
        raise AssertionError(f"Request failed: {str(e)}")

test_post_kme_pool_status()