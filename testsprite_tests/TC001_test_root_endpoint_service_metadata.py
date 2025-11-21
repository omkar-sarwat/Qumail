import requests

def test_root_endpoint_service_metadata():
    base_url = "http://localhost:9010"
    try:
        response = requests.get(f"{base_url}/", timeout=30)
    except requests.exceptions.RequestException as e:
        assert False, f"Request to root endpoint failed: {e}"
    assert response.status_code == 200, f"Expected HTTP 200 but got {response.status_code}"
    try:
        # The root endpoint should return service metadata as JSON
        json_data = response.json()
    except ValueError:
        assert False, "Response is not valid JSON"
    # Validate that essential metadata fields are present and correct
    assert isinstance(json_data, dict), "Response JSON is not an object"
    meta = json_data.get("meta")
    assert isinstance(meta, dict), "'meta' field missing or not an object in response"
    assert meta.get("project") == "QuMail-KMS", "Unexpected project name in meta"
    assert "date" in meta and isinstance(meta["date"], str), "'date' missing or not string in meta"
    assert "prepared_by" in meta and isinstance(meta["prepared_by"], str), "'prepared_by' missing or not string in meta"

test_root_endpoint_service_metadata()