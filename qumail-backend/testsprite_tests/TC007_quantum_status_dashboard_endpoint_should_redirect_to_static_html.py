import requests

BASE_URL = "http://localhost:8000"


def test_quantum_status_dashboard_endpoint_should_redirect_to_static_html():
    url = f"{BASE_URL}/quantum/status"
    try:
        response = requests.get(url, timeout=30, allow_redirects=False)
    except requests.RequestException as e:
        assert False, f"Request failed: {e}"

    assert response.status_code == 307, f"Expected status code 307, got {response.status_code}"
    # According to HTTP spec, Location header should indicate the redirect target
    location = response.headers.get("Location")
    assert location is not None, "Missing Location header for redirect"
    # Location should point to the static quantum status dashboard HTML page
    # Given PRD suggests /app/static/quantum_status.html - typically under /static/quantum_status.html
    assert "quantum_status" in location and location.endswith(".html"), f"Unexpected redirect location: {location}"


test_quantum_status_dashboard_endpoint_should_redirect_to_static_html()