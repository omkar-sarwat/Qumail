import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_encryption_status_endpoint_returns_real_time_quantum_key_metrics():
    url = f"{BASE_URL}/encryption/status"
    headers = {
        "Accept": "application/json"
    }
    try:
        response = requests.get(url, headers=headers, timeout=TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as e:
        assert False, f"Request to {url} failed: {e}"

    assert response.status_code == 200, f"Expected status code 200 but got {response.status_code}"

    resp_json = response.json()

    # Validate top-level keys presence
    expected_keys = [
        "kmeStatus",
        "quantumKeysAvailable",
        "encryptionStats",
        "entropyStatus",
        "averageEntropy",
        "keyUsage",
        "securityLevels",
        "timestamp",
        "systemStatus"
    ]
    for key in expected_keys:
        assert key in resp_json, f"Response JSON missing expected key: {key}"

    # Validate kmeStatus is a non-empty list of dicts with required fields
    kme_status_list = resp_json["kmeStatus"]
    assert isinstance(kme_status_list, list), "kmeStatus should be a list"
    assert len(kme_status_list) > 0, "kmeStatus list should not be empty"
    kme_required_keys = {"id", "name", "status", "latency", "keysAvailable", "maxKeySize", "averageEntropy", "keyGenRate", "zone"}
    for kme in kme_status_list:
        assert isinstance(kme, dict), "Each kmeStatus item should be a dict"
        missing = kme_required_keys - kme.keys()
        assert not missing, f"kmeStatus item missing keys: {missing}"
        # Validate field types
        assert isinstance(kme["id"], str)
        assert isinstance(kme["name"], str)
        assert isinstance(kme["status"], str)
        assert isinstance(kme["latency"], (int, float))
        assert isinstance(kme["keysAvailable"], int)
        assert isinstance(kme["maxKeySize"], int)
        assert isinstance(kme["averageEntropy"], (int, float))
        assert isinstance(kme["keyGenRate"], (int, float))
        assert isinstance(kme["zone"], str)

    # Validate quantumKeysAvailable is int >= 0
    assert isinstance(resp_json["quantumKeysAvailable"], int)
    assert resp_json["quantumKeysAvailable"] >= 0

    # Validate encryptionStats fields with int values
    encryption_stats = resp_json["encryptionStats"]
    assert isinstance(encryption_stats, dict)
    expected_enc_stats_keys = {"quantum_otp", "quantum_aes", "post_quantum", "standard_rsa"}
    missing_enc_keys = expected_enc_stats_keys - encryption_stats.keys()
    assert not missing_enc_keys, f"encryptionStats missing keys: {missing_enc_keys}"
    for key in expected_enc_stats_keys:
        assert isinstance(encryption_stats[key], int)
        assert encryption_stats[key] >= 0

    # Validate entropyStatus is a string
    assert isinstance(resp_json["entropyStatus"], str)

    # Validate averageEntropy is a number (int or float)
    assert isinstance(resp_json["averageEntropy"], (int, float))

    # Validate keyUsage is an array (content unspecified)
    assert isinstance(resp_json["keyUsage"], list)

    # Validate securityLevels is an object (dict)
    assert isinstance(resp_json["securityLevels"], dict)

    # Validate timestamp is a string (ISO8601 or similar)
    assert isinstance(resp_json["timestamp"], str)
    assert len(resp_json["timestamp"]) > 0

    # Validate systemStatus is a string
    assert isinstance(resp_json["systemStatus"], str)

test_encryption_status_endpoint_returns_real_time_quantum_key_metrics()