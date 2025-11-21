import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_generate_quantum_keys_endpoint_creates_keys_on_both_kmes():
    url = f"{BASE_URL}/api/v1/quantum/generate-keys"
    requested_count = 15
    params = {"count": requested_count}
    headers = {
        "Accept": "application/json",
        # Assuming OAuth 2.0 Bearer token is required; replace with valid token if needed
        # "Authorization": "Bearer YOUR_ACCESS_TOKEN_HERE"
    }

    try:
        response = requests.post(url, params=params, headers=headers, timeout=TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as e:
        raise AssertionError(f"Request failed: {e}")

    json_resp = response.json()

    # Assert top-level keys present
    expected_keys = {
        "success",
        "requestedKeys",
        "kme1",
        "kme2",
        "total",
        "keyTimestamps",
        "generatedAt",
    }
    assert expected_keys.issubset(json_resp.keys()), "Missing keys in response"

    # Validate success and requestedKeys
    assert isinstance(json_resp["success"], bool), "success must be boolean"
    assert json_resp["success"] is True, "success must be True"

    assert isinstance(json_resp["requestedKeys"], int), "requestedKeys must be int"
    assert json_resp["requestedKeys"] == requested_count, "requestedKeys mismatch"

    # Helper to validate KME stats object
    def validate_kme_stats(kme_obj):
        required = {"generated", "successful", "failedKeys", "successRate"}
        assert required.issubset(kme_obj.keys()), f"Missing keys in KME stats: {required - kme_obj.keys()}"

        assert isinstance(kme_obj["generated"], int), "generated must be int"
        assert isinstance(kme_obj["successful"], int), "successful must be int"
        assert isinstance(kme_obj["failedKeys"], int), "failedKeys must be int"
        assert 0.0 <= kme_obj["successRate"] <= 1.0, "successRate must be between 0 and 1"

        # Logical consistency checks
        assert kme_obj["generated"] >= 0
        assert kme_obj["successful"] >= 0
        assert kme_obj["failedKeys"] >= 0
        assert kme_obj["generated"] == kme_obj["successful"] + kme_obj["failedKeys"], "generated != successful + failedKeys"

    # Validate KME1 and KME2 stats
    validate_kme_stats(json_resp["kme1"])
    validate_kme_stats(json_resp["kme2"])
    validate_kme_stats(json_resp["total"])

    # Validate total counts consistency
    total = json_resp["total"]
    kme1 = json_resp["kme1"]
    kme2 = json_resp["kme2"]

    assert total["generated"] == kme1["generated"] + kme2["generated"], "Total generated mismatch"
    assert total["successful"] == kme1["successful"] + kme2["successful"], "Total successful mismatch"
    assert total["failedKeys"] == kme1["failedKeys"] + kme2["failedKeys"], "Total failedKeys mismatch"

    # Validate keyTimestamps is list of strings (ISO8601 or similar)
    key_timestamps = json_resp["keyTimestamps"]
    assert isinstance(key_timestamps, list), "keyTimestamps must be a list"
    assert all(isinstance(ts, str) and ts for ts in key_timestamps), "All keyTimestamps must be non-empty strings"
    assert len(key_timestamps) >= 0

    # Validate generatedAt is a non-empty string (timestamp)
    generated_at = json_resp["generatedAt"]
    assert isinstance(generated_at, str) and generated_at, "generatedAt must be a non-empty string"

test_generate_quantum_keys_endpoint_creates_keys_on_both_kmes()