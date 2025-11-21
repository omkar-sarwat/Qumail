import requests
import uuid

BASE_URL = "http://localhost:8000"
SEND_EMAIL_ENDPOINT = f"{BASE_URL}/emails/send"
DELETE_EMAIL_ENDPOINT = f"{BASE_URL}/emails"  # Assuming DELETE /emails/{emailId} is supported for cleanup
TIMEOUT = 30

# Deterministic bearer token accepted by the backend for integration tests
AUTH_TOKEN = "VALID_ACCESS_TOKEN"

# For authentication, assuming OAuth2 bearer token if required.
# Placeholder function to get valid auth headers; update with actual auth method as needed.
def get_auth_headers():
    return {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json"
    }


def test_send_encrypted_email_should_process_and_return_encryption_metadata():
    subject = f"Test Quantum Email {uuid.uuid4()}"
    body = "This is a test email body with quantum encryption."
    recipient = "recipient@example.com"
    security_level = 2  # Can be 1 to 4; using 2 as default valid

    payload = {
        "subject": subject,
        "body": body,
        "recipient": recipient,
        "securityLevel": security_level,
    }

    headers = get_auth_headers()

    email_id = None

    try:
        resp = requests.post(
            SEND_EMAIL_ENDPOINT,
            json=payload,
            headers=headers,
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200, f"Expected status code 200, got {resp.status_code}"
        data = resp.json()

        # Response must include success True
        assert isinstance(data.get("success"), bool), "Missing or invalid 'success' field"
        assert data["success"] is True, "Email send was not successful"

        # Required metadata fields
        required_fields = [
            "emailId",
            "flowId",
            "encryptionMethod",
            "securityLevel",
            "entropy",
            "keyId",
            "encryptedSize",
            "timestamp",
            "message",
        ]

        for field in required_fields:
            assert field in data, f"Missing field '{field}' in response"

        # Validate types of metadata fields
        assert isinstance(data["emailId"], int), "'emailId' should be int"
        assert isinstance(data["flowId"], str) and data["flowId"], "'flowId' should be non-empty string"
        assert isinstance(data["encryptionMethod"], str) and data["encryptionMethod"], "'encryptionMethod' should be non-empty string"
        assert isinstance(data["securityLevel"], int) and 1 <= data["securityLevel"] <= 4, "'securityLevel' should be int 1-4"
        assert isinstance(data["entropy"], (float, int)), "'entropy' should be a number"
        assert isinstance(data["keyId"], str) and data["keyId"], "'keyId' should be non-empty string"
        assert isinstance(data["encryptedSize"], int) and data["encryptedSize"] > 0, "'encryptedSize' should be positive int"
        assert isinstance(data["timestamp"], str) and data["timestamp"], "'timestamp' should be non-empty string"
        assert isinstance(data["message"], str), "'message' should be string"

        email_id = data["emailId"]

    finally:
        # Cleanup: delete the sent email to keep test environment clean if DELETE endpoint supported
        if email_id is not None:
            try:
                delete_resp = requests.delete(
                    f"{DELETE_EMAIL_ENDPOINT}/{email_id}",
                    headers=headers,
                    timeout=TIMEOUT,
                )
                # Accept 200 or 204 as successful delete
                assert delete_resp.status_code in (200, 204), f"Failed to delete email {email_id}"
            except Exception:
                pass


test_send_encrypted_email_should_process_and_return_encryption_metadata()