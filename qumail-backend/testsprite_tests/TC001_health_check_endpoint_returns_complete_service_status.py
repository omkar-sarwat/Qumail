import requests

def test_health_check_endpoint_returns_complete_service_status():
    base_url = "http://localhost:8000"
    url = f"{base_url}/health"
    timeout = 30
    headers = {
        "Accept": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, timeout=timeout)
    except requests.RequestException as e:
        assert False, f"Request to /health endpoint failed: {e}"

    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    try:
        data = response.json()
    except ValueError:
        assert False, "Response is not valid JSON"

    # Validate keys in response JSON
    expected_keys = {"healthy", "services", "version", "timestamp", "uptime_seconds"}
    assert expected_keys.issubset(data.keys()), f"Response JSON missing keys from {expected_keys}"

    services = data.get("services")
    assert isinstance(services, dict), "services should be a JSON object"
    expected_services = {"database", "km_server_1", "km_server_2", "security_auditor"}
    assert expected_services.issubset(services.keys()), f"services object missing keys: {expected_services}"

    # Validate types of each expected key
    assert isinstance(data["healthy"], bool), "healthy should be a boolean"
    assert all(isinstance(services[srv], str) for srv in expected_services), "All service statuses should be strings"
    assert isinstance(data["version"], str), "version should be a string"
    assert isinstance(data["timestamp"], str), "timestamp should be a string"
    assert isinstance(data["uptime_seconds"], (int, float)), "uptime_seconds should be a number"

test_health_check_endpoint_returns_complete_service_status()