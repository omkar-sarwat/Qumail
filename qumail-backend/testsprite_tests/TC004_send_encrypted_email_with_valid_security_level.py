import requests
import random
import string

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

# NOTE: Replace 'YOUR_ACCESS_TOKEN' with a valid OAuth 2.0 access token for the test environment


def test_send_encrypted_email_with_valid_security_level():
    url = f"{BASE_URL}/emails/send"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer YOUR_ACCESS_TOKEN"
    }
    # Prepare a valid security level between 1 and 4
    security_level = random.randint(1, 4)

    # Generate random subject and body to avoid duplication and for uniqueness
    random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    payload = {
        "subject": f"Test Email Subject {random_str}",
        "body": f"This is the body of the test encrypted email at security level {security_level}.",
        "recipient": "testrecipient@example.com",
        "securityLevel": security_level
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=TIMEOUT)
    except requests.RequestException as e:
        assert False, f"Request to send encrypted email failed with exception: {e}"

    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"

    try:
        resp_json = response.json()
    except ValueError:
        assert False, "Response is not valid JSON"

    # Validate success flag
    assert "success" in resp_json, "Response missing 'success' key"
    assert resp_json["success"] is True, "Email sending not successful"

    # Validate required fields presence and types
    expected_fields = {
        "emailId": int,
        "flowId": str,
        "encryptionMethod": str,
        "securityLevel": int,
        "entropy": (float, int),
        "keyId": str,
        "encryptedSize": int,
        "timestamp": str,
        "message": str,
    }
    for field, ftype in expected_fields.items():
        assert field in resp_json, f"Response missing '{field}' key"
        assert isinstance(resp_json[field], ftype), f"Field '{field}' expected type {ftype} but got type {type(resp_json[field])}"

    # Validate that the returned securityLevel matches the requested one
    assert resp_json["securityLevel"] == security_level, (
        f"Returned securityLevel {resp_json['securityLevel']} does not match requested {security_level}"
    )

test_send_encrypted_email_with_valid_security_level()
