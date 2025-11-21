import requests


def test_root_endpoint_should_return_api_information_and_features():
    url = "http://localhost:8000/"
    timeout = 30
    try:
        response = requests.get(url, timeout=timeout)
    except requests.RequestException as e:
        assert False, f"Request to root endpoint failed: {e}"

    assert response.status_code == 200, f"Expected status code 200 but got {response.status_code}"
    try:
        data = response.json()
    except ValueError:
        assert False, "Response is not in JSON format"

    # Check required fields presence and types
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
        assert field in data, f"Missing '{field}' in response"
        assert isinstance(data[field], expected_type), f"Field '{field}' expected type {expected_type.__name__} but got {type(data[field]).__name__}"

    # Additional checks on contents for security_levels and features as list of strings
    assert all(isinstance(item, str) for item in data["security_levels"]), "'security_levels' must be a list of strings"
    assert all(isinstance(item, str) for item in data["features"]), "'features' must be a list of strings"


test_root_endpoint_should_return_api_information_and_features()