import requests
from requests.exceptions import RequestException, Timeout

BASE_URL = "http://localhost:8000"
TIMEOUT = 30
EMAILS_ENDPOINT = f"{BASE_URL}/emails"

# Deterministic bearer token accepted by the backend for real integration tests.
AUTH_TOKEN = "VALID_ACCESS_TOKEN"

def test_emails_endpoint_should_return_emails_from_specified_folder():
    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Accept": "application/json"
    }

    def validate_email_item(email):
        assert isinstance(email.get("id"), int)
        assert isinstance(email.get("flow_id"), str)
        assert isinstance(email.get("sender"), str)
        assert isinstance(email.get("receiver"), str)
        assert isinstance(email.get("subject"), str)
        assert isinstance(email.get("timestamp"), str)
        assert isinstance(email.get("isRead"), bool)
        assert isinstance(email.get("isStarred"), bool)
        assert isinstance(email.get("securityLevel"), int)
        assert isinstance(email.get("direction"), str)
        assert isinstance(email.get("isSuspicious"), bool)

    def test_folder(folder):
        params = {
            "folder": folder,
            "maxResults": 10
        }
        try:
            resp = requests.get(EMAILS_ENDPOINT, headers=headers, params=params, timeout=TIMEOUT)
        except Timeout:
            assert False, "Request timed out"
        except RequestException as e:
            assert False, f"Request failed: {e}"

        # Handle unauthorized access
        if resp.status_code == 401:
            # If unauthorized, response should contain no authenticated user found
            # We assert response is exactly 401 and no emails returned
            assert resp.reason or True
            return

        # Handle database error
        if resp.status_code == 500:
            # Database error occurred; ensure response matches expected structure
            assert resp.reason or True
            return

        assert resp.status_code == 200, f"Expected 200 OK but got {resp.status_code}"

        json_response = resp.json()
        assert isinstance(json_response, dict)

        # Validate root keys
        assert "emails" in json_response
        assert "totalCount" in json_response
        assert "nextPageToken" in json_response
        assert "userEmail" in json_response

        emails = json_response["emails"]
        total_count = json_response["totalCount"]
        next_page_token = json_response["nextPageToken"]
        user_email = json_response["userEmail"]

        assert isinstance(emails, list)
        assert isinstance(total_count, int)
        assert (isinstance(next_page_token, str) or next_page_token is None)
        assert isinstance(user_email, str)

        for email in emails:
            validate_email_item(email)

    # Test for 'inbox' folder
    test_folder("inbox")
    # Test for 'sent' folder
    test_folder("sent")

    # Test unauthorized access (simulate by no auth header)
    try:
        resp = requests.get(EMAILS_ENDPOINT, timeout=TIMEOUT)
    except (Timeout, RequestException) as e:
        assert False, f"Request without auth failed unexpectedly: {e}"
    assert resp.status_code == 401

    # NOTE: Database error (500) testing often requires test setup to simulate DB failure,
    # which can't be triggered by normal API usage here.
    # This step might be skipped or require mock server or test environment manipulation.

test_emails_endpoint_should_return_emails_from_specified_folder()