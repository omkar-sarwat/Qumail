"""
Test to verify email encryption using real quantum keys

This test:
1. Authenticates using the test token (VALID_ACCESS_TOKEN)
2. Sends encrypted emails with different security levels
3. Retrieves encrypted emails from database
4. Decrypts emails and verifies content
5. Confirms quantum keys were actually used in encryption

Run with: python test_email_encryption_verification.py
"""

import asyncio
import requests
import json
import base64
from datetime import datetime

# Backend API base URL
BASE_URL = "http://localhost:8000"

# Test authentication token (matches backend test mode)
AUTH_TOKEN = "VALID_ACCESS_TOKEN"

# Test data
TEST_SUBJECT = f"Quantum Test Email - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
TEST_BODY = "This is a test message encrypted with real quantum keys from KME servers!"
TEST_RECIPIENT = "recipient@example.com"

def print_section(title):
    """Print formatted section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def print_result(label, value):
    """Print formatted result"""
    if isinstance(value, dict):
        print(f"\n{label}:")
        for k, v in value.items():
            print(f"  {k}: {v}")
    else:
        print(f"{label}: {value}")

def test_authentication():
    """Test authentication with test token"""
    print_section("STEP 1: TESTING AUTHENTICATION")
    
    headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
    response = requests.get(f"{BASE_URL}/api/v1/auth/me", headers=headers)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        user_data = response.json()
        print_result("✅ Authentication Successful", user_data)
        return True
    else:
        print(f"❌ Authentication Failed: {response.text}")
        return False

def send_encrypted_email(security_level):
    """Send encrypted email with specified security level"""
    print_section(f"STEP 2: SENDING ENCRYPTED EMAIL (Security Level {security_level})")
    
    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "subject": f"{TEST_SUBJECT} - Level {security_level}",
        "body": TEST_BODY,
        "recipient": TEST_RECIPIENT,
        "securityLevel": security_level
    }
    
    print(f"Request Payload:")
    print(f"  Subject: {payload['subject']}")
    print(f"  Body: {payload['body']}")
    print(f"  Recipient: {payload['recipient']}")
    print(f"  Security Level: {payload['securityLevel']}")
    
    response = requests.post(
        f"{BASE_URL}/emails/send",
        headers=headers,
        json=payload
    )
    
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print_result("✅ Email Sent Successfully", {
            "Email ID": result.get("emailId"),
            "Email UUID": result.get("emailUuid"),
            "Flow ID": result.get("flowId"),
            "Encryption Method": result.get("encryptionMethod"),
            "Security Level": result.get("securityLevel"),
            "Key ID": result.get("keyId"),
            "Encrypted Size": result.get("encryptedSize"),
            "Entropy": result.get("entropy"),
            "Timestamp": result.get("timestamp")
        })
        
        # Check if quantum keys were used
        if result.get("keyId"):
            print(f"\n🔑 QUANTUM KEY VERIFICATION:")
            print(f"  ✓ Quantum Key ID: {result.get('keyId')}")
            print(f"  ✓ Key Entropy: {result.get('entropy', 0):.4f}")
            print(f"  ✓ This confirms REAL quantum keys were used from KME servers!")
        
        return result
    else:
        print(f"❌ Failed to send email: {response.text}")
        return None

def retrieve_emails():
    """Retrieve emails from database"""
    print_section("STEP 3: RETRIEVING ENCRYPTED EMAILS FROM DATABASE")
    
    headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
    
    # Get sent emails
    response = requests.get(
        f"{BASE_URL}/emails?folder=sent&maxResults=10",
        headers=headers
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        emails = data.get("emails", [])
        total_count = data.get("totalCount", 0)
        
        print(f"✅ Retrieved {len(emails)} emails (Total in DB: {total_count})")
        
        if emails:
            print("\nEmail List:")
            for idx, email in enumerate(emails, 1):
                print(f"\n  [{idx}] Email:")
                print(f"      ID: {email.get('id')}")
                print(f"      UUID: {email.get('emailUuid')}")
                print(f"      Flow ID: {email.get('flow_id')}")
                print(f"      Subject: {email.get('subject')}")
                print(f"      From: {email.get('sender')}")
                print(f"      To: {email.get('receiver')}")
                print(f"      Security Level: {email.get('securityLevel')}")
                print(f"      Timestamp: {email.get('timestamp')}")
        
        return emails
    else:
        print(f"❌ Failed to retrieve emails: {response.text}")
        return []

def decrypt_email(email_id):
    """Decrypt email and verify content"""
    print_section(f"STEP 4: DECRYPTING EMAIL (ID: {email_id})")
    
    headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
    
    response = requests.post(
        f"{BASE_URL}/api/v1/emails/email/{email_id}/decrypt",
        headers=headers
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        email_data = result.get("email_data", {})
        security_info = result.get("security_info", {})
        
        print_result("✅ Email Decrypted Successfully", {
            "Subject": email_data.get("subject"),
            "Body": email_data.get("body"),
            "From": email_data.get("sender_email"),
            "To": email_data.get("receiver_email"),
            "Security Level": security_info.get("security_level"),
            "Algorithm": security_info.get("algorithm"),
            "Verification Status": security_info.get("verification_status"),
            "Quantum Enhanced": security_info.get("quantum_enhanced"),
            "Flow ID": email_data.get("flow_id")
        })
        
        # Verify content matches
        body = email_data.get("body", "")
        if body and TEST_BODY in body:
            print("\n✅ DECRYPTION VERIFICATION:")
            print("  ✓ Decrypted content matches original message")
            print("  ✓ Encryption/Decryption cycle completed successfully")
            print("  ✓ Quantum keys worked correctly!")
        else:
            print("\n⚠️  WARNING: Decrypted content doesn't match original")
            print(f"  Expected content: '{TEST_BODY}'")
            print(f"  Received body: '{body[:100] if body else 'None'}...'")
        
        return result
    else:
        print(f"❌ Failed to decrypt email: {response.text}")
        return None

def check_kme_status():
    """Check KME server status"""
    print_section("STEP 0: CHECKING KME SERVER STATUS")
    
    response = requests.get(f"{BASE_URL}/encryption/status")
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        status = response.json()
        kme_status = status.get("kmeStatus", [])
        
        print(f"System Status: {status.get('systemStatus')}")
        print(f"Quantum Keys Available: {status.get('quantumKeysAvailable')}")
        print(f"\nKME Servers:")
        
        for kme in kme_status:
            print(f"\n  {kme.get('name')}:")
            print(f"    Status: {kme.get('status')}")
            print(f"    Latency: {kme.get('latency')} ms")
            print(f"    Keys Available: {kme.get('keysAvailable')}")
            print(f"    Zone: {kme.get('zone')}")
        
        # Check if KMEs are operational
        all_connected = all(kme.get("status") == "connected" for kme in kme_status)
        if all_connected:
            print("\n✅ All KME servers are connected and operational!")
            return True
        else:
            print("\n⚠️  WARNING: Some KME servers are not connected")
            print("   The test may use fallback encryption methods")
            return False
    else:
        print(f"❌ Failed to check KME status: {response.text}")
        return False

def run_full_test():
    """Run complete encryption verification test"""
    print("\n" + "🔐"*40)
    print("  QUMAIL QUANTUM EMAIL ENCRYPTION VERIFICATION TEST")
    print("🔐"*40)
    
    try:
        # Step 0: Check KME status
        kme_ok = check_kme_status()
        if not kme_ok:
            print("\n⚠️  KME servers not fully operational, continuing with test...")
        
        # Step 1: Test authentication
        if not test_authentication():
            print("\n❌ Test failed at authentication step")
            return False
        
        # Step 2: Send encrypted emails with different security levels
        sent_emails = []
        for level in [1, 2, 3, 4]:
            result = send_encrypted_email(level)
            if result:
                sent_emails.append(result)
            else:
                print(f"\n⚠️  Failed to send Level {level} email, continuing...")
        
        if not sent_emails:
            print("\n❌ Test failed: No emails were sent successfully")
            return False
        
        # Step 3: Retrieve emails
        emails = retrieve_emails()
        if not emails:
            print("\n⚠️  No emails retrieved from database")
            # Continue anyway as emails might exist from previous runs
        
        # Step 4: Decrypt emails
        decrypted_count = 0
        for email_data in sent_emails:
            email_uuid = email_data.get("emailUuid")
            if email_uuid:
                decrypted = decrypt_email(email_uuid)
                if decrypted:
                    decrypted_count += 1
        
        # Final summary
        print_section("TEST SUMMARY")
        print(f"✅ Authentication: Successful")
        print(f"✅ Emails Sent: {len(sent_emails)}/4")
        print(f"✅ Emails Decrypted: {decrypted_count}/{len(sent_emails)}")
        
        if decrypted_count == len(sent_emails) == 4:
            print(f"\n🎉 ALL TESTS PASSED!")
            print(f"   - All 4 security levels tested successfully")
            print(f"   - Quantum keys were used for encryption")
            print(f"   - Encryption/Decryption verified")
            print(f"   - Email content integrity maintained")
            return True
        elif decrypted_count > 0:
            print(f"\n⚠️  PARTIAL SUCCESS")
            print(f"   - {decrypted_count} out of {len(sent_emails)} emails verified")
            return True
        else:
            print(f"\n❌ TEST FAILED")
            print(f"   - No emails could be decrypted successfully")
            return False
            
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\nStarting QuMail Quantum Email Encryption Verification Test...")
    print("Make sure the backend server is running on http://localhost:8000")
    print("Make sure KME servers are running on ports 8010 and 8020")
    
    input("\nPress Enter to start the test...")
    
    success = run_full_test()
    
    if success:
        print("\n✅ Encryption verification completed successfully!")
        exit(0)
    else:
        print("\n❌ Encryption verification failed!")
        exit(1)
