import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_health_check_endpoint_should_return_all_service_statuses():
    url = f"{BASE_URL}/health"
    try:
        response = requests.get(url, timeout=TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as e:
        assert False, f"Request failed: {e}"
    
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    
    try:
        data = response.json()
    except ValueError:
        assert False, "Response is not a valid JSON"
    
    # Validate top-level keys existence and types
    expected_keys = {"healthy", "services", "version", "timestamp", "uptime_seconds"}
    assert expected_keys.issubset(data.keys()), f"Missing expected keys in response: {expected_keys - data.keys()}"
    
    assert isinstance(data["healthy"], bool), "'healthy' should be boolean"
    assert isinstance(data["version"], str) and data["version"], "'version' should be a non-empty string"
    assert isinstance(data["timestamp"], str) and data["timestamp"], "'timestamp' should be a non-empty string"
    assert isinstance(data["uptime_seconds"], (int, float)), "'uptime_seconds' should be a number"
    
    services = data["services"]
    assert isinstance(services, dict), "'services' should be a dictionary"
    
    service_keys = {"database", "km_server_1", "km_server_2", "security_auditor"}
    assert service_keys.issubset(services.keys()), f"Missing expected service keys: {service_keys - services.keys()}"
    
    for key in service_keys:
        assert isinstance(services[key], str) and services[key], f"Service '{key}' status should be a non-empty string"

test_health_check_endpoint_should_return_all_service_statuses()