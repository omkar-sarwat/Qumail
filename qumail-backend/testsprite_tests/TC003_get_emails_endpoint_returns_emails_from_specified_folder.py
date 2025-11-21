import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_get_emails_from_specified_folder():
    url = f"{BASE_URL}/emails"
    headers = {
        "Accept": "application/json",
        "Authorization": "Bearer VALID_ACCESS_TOKEN"
    }
    params = {
        "folder": "inbox",
        "maxResults": 50
    }

    response = None
    try:
        response = requests.get(url, headers=headers, params=params, timeout=TIMEOUT)
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        data = response.json()

        # Validate main response keys
        assert isinstance(data, dict), "Response JSON must be an object"
        assert "emails" in data, "'emails' key missing in response"
        assert "totalCount" in data, "'totalCount' key missing in response"
        assert "nextPageToken" in data, "'nextPageToken' key missing in response"
        assert "userEmail" in data, "'userEmail' key missing in response"

        emails = data["emails"]
        assert isinstance(emails, list), "'emails' must be a list"
        total_count = data["totalCount"]
        assert isinstance(total_count, int), "'totalCount' must be an integer"
        next_page_token = data["nextPageToken"]
        assert isinstance(next_page_token, (str, type(None))), "'nextPageToken' must be string or null"
        user_email = data["userEmail"]
        assert isinstance(user_email, str), "'userEmail' must be a string"

        # Validate each email metadata
        expected_keys = {
            "id": int,
            "flow_id": str,
            "sender": str,
            "receiver": str,
            "subject": str,
            "timestamp": str,
            "isRead": bool,
            "isStarred": bool,
            "securityLevel": int,
            "direction": str,
            "isSuspicious": bool
        }
        for email in emails:
            assert isinstance(email, dict), "Each email must be an object"
            for key, expected_type in expected_keys.items():
                assert key in email, f"Email is missing key '{key}'"
                value = email[key]
                # Allow None for string fields if any edge cases
                if expected_type == str:
                    assert (value is None) or isinstance(value, str), f"Email key '{key}' must be string or None"
                else:
                    assert isinstance(value, expected_type), f"Email key '{key}' must be of type {expected_type.__name__}"
    except requests.exceptions.RequestException as e:
        assert False, f"Request failed: {e}"

test_get_emails_from_specified_folder()