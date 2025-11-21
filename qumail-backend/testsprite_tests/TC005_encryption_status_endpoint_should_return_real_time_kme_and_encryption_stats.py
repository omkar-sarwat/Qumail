import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_encryption_status_endpoint_should_return_real_time_kme_and_encryption_stats():
    url = f"{BASE_URL}/encryption/status"
    headers = {
        "Accept": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, timeout=TIMEOUT)
    except requests.RequestException as e:
        assert False, f"Request to /encryption/status failed: {e}"

    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"

    try:
        data = response.json()
    except ValueError:
        assert False, "Response is not valid JSON"

    # Validate presence and types of required fields
    # kmeStatus: array of objects with specific fields
    assert "kmeStatus" in data and isinstance(data["kmeStatus"], list), "Missing or invalid kmeStatus"
    for item in data["kmeStatus"]:
        assert isinstance(item, dict), "Each kmeStatus item should be a dict"
        for key in ["id", "name", "status", "latency", "keysAvailable", "maxKeySize", "averageEntropy", "keyGenRate", "zone"]:
            assert key in item, f"Missing '{key}' in kmeStatus item"
        assert isinstance(item["id"], str)
        assert isinstance(item["name"], str)
        assert isinstance(item["status"], str)
        assert isinstance(item["latency"], (float, int))
        assert isinstance(item["keysAvailable"], int)
        assert isinstance(item["maxKeySize"], int)
        assert isinstance(item["averageEntropy"], (float, int))
        assert isinstance(item["keyGenRate"], (float, int))
        assert isinstance(item["zone"], str)

    # quantumKeysAvailable: integer
    assert "quantumKeysAvailable" in data and isinstance(data["quantumKeysAvailable"], int)

    # encryptionStats: object with specified integer fields
    expected_encryption_stats_keys = {"quantum_otp", "quantum_aes", "post_quantum", "standard_rsa"}
    assert "encryptionStats" in data and isinstance(data["encryptionStats"], dict)
    for key in expected_encryption_stats_keys:
        assert key in data["encryptionStats"], f"Missing '{key}' in encryptionStats"
        assert isinstance(data["encryptionStats"][key], int)

    # entropyStatus: string
    assert "entropyStatus" in data and isinstance(data["entropyStatus"], str)

    # averageEntropy: number (float or int)
    assert "averageEntropy" in data and isinstance(data["averageEntropy"], (float, int))

    # keyUsage: array (content unknown, just check it's a list)
    assert "keyUsage" in data and isinstance(data["keyUsage"], list)

    # securityLevels: object (content unknown, check dict)
    assert "securityLevels" in data and isinstance(data["securityLevels"], dict)

    # timestamp: string
    assert "timestamp" in data and isinstance(data["timestamp"], str)

    # systemStatus: string
    assert "systemStatus" in data and isinstance(data["systemStatus"], str)

test_encryption_status_endpoint_should_return_real_time_kme_and_encryption_stats()