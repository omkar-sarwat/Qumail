import requests
import time

BASE_ENDPOINT_KMS1 = "http://127.0.0.1:9010"
BASE_ENDPOINT_KMS2 = "http://127.0.0.1:9020"
TIMEOUT_SECONDS = 5

HEADERS_KMS1_TO_KMS2 = {
    "X-SAE-ID": "25840139-0dd4-49ae-ba1e-b86731601803",
    "X-Slave-SAE-ID": "c565d5aa-8670-4446-8471-b0e53e315d2a",
    "Connection": "close"
}

HEADERS_KMS2_TO_KMS1 = {
    "X-SAE-ID": "c565d5aa-8670-4446-8471-b0e53e315d2a",
    "X-Slave-SAE-ID": "25840139-0dd4-49ae-ba1e-b86731601803",
    "Connection": "close"
}

HEADERS_KMS1_KME = {
    "X-KMS-ID": "KMS-1",
    "Connection": "close"
}

HEADERS_KMS2_KME = {
    "X-KMS-ID": "KMS-2",
    "Connection": "close"
}


def test_post_dec_keys_request_decryption_keys():
    enc_keys_url = f"{BASE_ENDPOINT_KMS1}/api/v1/keys/enc_keys"
    kme_verify_url = f"{BASE_ENDPOINT_KMS2}/api/v1/kme/verify"
    dec_keys_url = f"{BASE_ENDPOINT_KMS2}/api/v1/keys/dec_keys"

    number_keys = 2
    key_size = 256
    payload_enc = {"number": number_keys, "size": key_size}

    for iteration in range(10):
        try:
            # Step 1: Request encryption keys from KMS-1
            start_enc = time.time()
            response_enc = requests.post(
                enc_keys_url,
                headers=HEADERS_KMS1_TO_KMS2,
                json=payload_enc,
                timeout=TIMEOUT_SECONDS,
            )
            elapsed_enc = time.time() - start_enc
            assert response_enc.status_code == 200, f"Enc keys request failed, status: {response_enc.status_code}"
            assert elapsed_enc <= 2, f"Encryption key request took too long: {elapsed_enc:.2f}s"

            data_enc = response_enc.json()
            # Validate keys array presence and length
            keys = data_enc.get("keys")
            assert isinstance(keys, list), "Response missing 'keys' list"
            assert len(keys) == number_keys, f"Expected {number_keys} keys but got {len(keys)}"

            # Extract key IDs for verification and decryption request
            key_ids = []
            for key_item in keys:
                kid = key_item.get("key_ID")
                assert isinstance(kid, str) and kid.strip(), "Invalid or missing key_ID"
                key_ids.append(kid)

            # Step 2: Verify keys on KMS-2 via /api/v1/kme/verify
            verify_payload = {"key_IDs": key_ids}
            start_verify = time.time()
            response_verify = requests.post(
                kme_verify_url,
                headers=HEADERS_KMS2_KME,
                json=verify_payload,
                timeout=TIMEOUT_SECONDS,
            )
            elapsed_verify = time.time() - start_verify
            assert response_verify.status_code == 200, f"KME verify request failed, status: {response_verify.status_code}"
            assert elapsed_verify <= 2, f"KME verify request took too long: {elapsed_verify:.2f}s"

            verify_data = response_verify.json()
            all_verified = verify_data.get("all_verified")
            assert all_verified is True, f"Keys not all verified on KMS-2: {verify_data}"

            # Step 3: Request decryption keys from KMS-2 with swapped headers
            dec_payload = {"key_IDs": key_ids}
            start_dec = time.time()
            response_dec = requests.post(
                dec_keys_url,
                headers=HEADERS_KMS2_TO_KMS1,
                json=dec_payload,
                timeout=TIMEOUT_SECONDS,
            )
            elapsed_dec = time.time() - start_dec
            assert response_dec.status_code == 200, f"Dec keys request failed, status: {response_dec.status_code}"
            assert elapsed_dec <= 2, f"Decryption key request took too long: {elapsed_dec:.2f}s"

            dec_data = response_dec.json()
            dec_keys = dec_data.get("keys")
            assert isinstance(dec_keys, list), "Response missing 'keys' list on decryption keys request"
            assert len(dec_keys) == number_keys, f"Expected {number_keys} decryption keys, got {len(dec_keys)}"

            # Confirm returned keys match requested key IDs and marked consumed
            returned_key_ids = [k.get("key_ID") for k in dec_keys if "key_ID" in k]
            assert set(returned_key_ids) == set(key_ids), "Returned decryption keys do not match requested key IDs"

            for key_obj in dec_keys:
                consumed = key_obj.get("consumed")
                assert consumed is True, "Decryption key not marked as consumed"

            # Step 4: Attempt to reuse keys (should not be reissued)
            # Request again decryption keys with the same IDs - expect failure or empty response or error
            reuse_payload = {"key_IDs": key_ids}
            try:
                reuse_response = requests.post(
                    dec_keys_url,
                    headers=HEADERS_KMS2_TO_KMS1,
                    json=reuse_payload,
                    timeout=TIMEOUT_SECONDS,
                )
            except requests.exceptions.RequestException as e:
                # If KMS-2 unreachable, report clearly
                raise RuntimeError(f"KMS-2 is not reachable during reuse check: {e}")

            # Validate reuse response: should not return keys as these are consumed
            if reuse_response.status_code == 200:
                reuse_data = reuse_response.json()
                reuse_keys = reuse_data.get("keys", [])
                # Should be empty or none of the requested keys should be returned
                if reuse_keys:
                    reuse_returned_key_ids = [k.get("key_ID") for k in reuse_keys if "key_ID" in k]
                    intersection = set(reuse_returned_key_ids).intersection(set(key_ids))
                    assert len(intersection) == 0, "Keys reused which should not happen"
            else:
                # If error returned (e.g. 400 or 404) it is acceptable behavior for reused keys
                assert reuse_response.status_code in (400, 404), f"Unexpected status for reused keys request: {reuse_response.status_code}"

        except requests.exceptions.ConnectionError:
            raise RuntimeError("KMS-2 service is not reachable at http://127.0.0.1:9020")

        except Exception:
            raise

test_post_dec_keys_request_decryption_keys()
