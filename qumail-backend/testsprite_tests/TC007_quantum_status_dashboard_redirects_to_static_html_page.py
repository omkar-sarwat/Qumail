import requests

BASE_URL = "http://localhost:8000"


def test_tc007_quantum_status_dashboard_redirect():
    url = f"{BASE_URL}/quantum/status"
    try:
        response = requests.get(url, timeout=30, allow_redirects=False)
    except requests.RequestException as e:
        assert False, f"Request to {url} failed with exception: {e}"

    # Assert response status code is 307 Temporary Redirect
    assert response.status_code == 307, (
        f"Expected status code 307 for redirect but got {response.status_code}"
    )

    # The Location header should be present and point to the static HTML page
    location = response.headers.get("location") or response.headers.get("Location")
    assert location is not None, "Redirect response missing Location header"

    # Check that the redirect location ends with 'quantum_status.html'
    assert location.endswith("quantum_status.html"), (
        f"Redirect location expected to end with 'quantum_status.html' but got: {location}"
    )


test_tc007_quantum_status_dashboard_redirect()