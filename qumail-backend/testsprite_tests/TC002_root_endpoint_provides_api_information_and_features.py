import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_root_endpoint_provides_api_information_and_features():
    url = f"{BASE_URL}/"
    try:
        response = requests.get(url, timeout=TIMEOUT)
    except requests.RequestException as e:
        assert False, f"Request to root endpoint failed: {e}"
    
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    
    try:
        data = response.json()
    except ValueError:
        assert False, "Response is not valid JSON"
    
    # Validate required fields existence and type
    required_fields = {
        "service": str,
        "version": str,
        "status": str,
        "environment": str,
        "documentation": str,
        "security_levels": list,
        "features": list,
        "timestamp": str
    }
    
    for field, expected_type in required_fields.items():
        assert field in data, f"Missing field '{field}' in response"
        assert isinstance(data[field], expected_type), f"Field '{field}' is not of type {expected_type.__name__}"
    
    # Validate security_levels and features list items type
    assert all(isinstance(item, str) for item in data["security_levels"]), "All items in 'security_levels' must be strings"
    assert all(isinstance(item, str) for item in data["features"]), "All items in 'features' must be strings"

test_root_endpoint_provides_api_information_and_features()