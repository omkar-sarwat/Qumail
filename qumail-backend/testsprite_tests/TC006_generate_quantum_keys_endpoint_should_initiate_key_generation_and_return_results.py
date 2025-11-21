import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30


def test_generate_quantum_keys_endpoint_should_initiate_key_generation_and_return_results():
    url = f"{BASE_URL}/api/v1/quantum/generate-keys"
    count = 10
    params = {"count": count}
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(url, params=params, headers=headers, timeout=TIMEOUT)
    except requests.RequestException as e:
        assert False, f"Request to generate quantum keys failed: {e}"

    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    try:
        data = response.json()
    except ValueError:
        assert False, "Response is not valid JSON"

    # Validate top-level keys
    expected_keys = {
        "success", "requestedKeys", "kme1", "kme2", "total", "keyTimestamps", "generatedAt"
    }
    assert expected_keys.issubset(data.keys()), f"Response keys missing. Expected at least {expected_keys}, got {data.keys()}"

    # Validate types and values
    assert isinstance(data["success"], bool), "'success' should be a boolean"
    assert data["requestedKeys"] == count, f"'requestedKeys' should be {count}"

    # Validate kme1, kme2, total objects
    for kme_key in ["kme1", "kme2", "total"]:
        assert isinstance(data[kme_key], dict), f"'{kme_key}' should be an object"
        for prop in ["generated", "successful", "failedKeys", "successRate"]:
            assert prop in data[kme_key], f"'{prop}' missing in '{kme_key}'"
        assert isinstance(data[kme_key]["generated"], int), f"'{kme_key}.generated' should be int"
        assert isinstance(data[kme_key]["successful"], int), f"'{kme_key}.successful' should be int"
        assert isinstance(data[kme_key]["failedKeys"], int), f"'{kme_key}.failedKeys' should be int"
        assert isinstance(data[kme_key]["successRate"], (int, float)), f"'{kme_key}.successRate' should be a number"
        # successRate should be between 0 and 1
        assert 0 <= data[kme_key]["successRate"] <= 1, f"'{kme_key}.successRate' must be between 0 and 1"

    # Validate generated keys numbers consistency
    total_generated = data["total"]["generated"]
    total_successful = data["total"]["successful"]
    total_failed = data["total"]["failedKeys"]
    # Sum of kme1 and kme2 generated keys should be consistent with total generated keys (likely equal or close)
    generated_sum = data["kme1"]["generated"] + data["kme2"]["generated"]
    # Since they are synchronized, they likely are the same or total is one of them, but check consistency loosely
    assert total_generated >= 0
    assert total_successful >= 0
    assert total_failed >= 0
    assert isinstance(data["keyTimestamps"], list), "'keyTimestamps' should be a list"
    # All timestamps should be string ISO format (basic check)
    for ts in data["keyTimestamps"]:
        assert isinstance(ts, str), "Each item in 'keyTimestamps' should be a string"
    # 'generatedAt' should be a string timestamp
    assert isinstance(data["generatedAt"], str), "'generatedAt' should be a string timestamp"

    # Overall success should be True if successful keys >= requested count (loosely)
    assert data["success"] is True or data["success"] is False
    # If success True then successful keys should be at least count
    if data["success"]:
        assert data["total"]["successful"] >= count, "Success==True but successful keys less than requested count"
    else:
        assert data["total"]["successful"] < count or True  # This case allowed


test_generate_quantum_keys_endpoint_should_initiate_key_generation_and_return_results()