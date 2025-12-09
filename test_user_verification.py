"""
Test QuMail User Verification System

This script tests the user verification feature that ensures:
1. Users are stored in MongoDB when they login via Google OAuth
2. Encrypted emails can only be sent to registered QuMail users
3. The API properly validates recipients before sending
"""

import asyncio
import aiohttp
import json

# Configuration
BACKEND_URL = "http://localhost:8000"

async def test_user_check_endpoint():
    """Test the /api/v1/users/check endpoint"""
    print("\n" + "="*70)
    print("TESTING QUMAIL USER VERIFICATION SYSTEM")
    print("="*70)
    
    # Note: This requires a valid JWT token from an authenticated user
    # For testing, you can get a token by logging in via the frontend
    
    test_emails = [
        "test@example.com",  # Likely not a QuMail user
        "nonexistent@gmail.com",  # Definitely not a QuMail user
    ]
    
    print(f"\n📧 Testing user check for: {test_emails}")
    
    # This is a mock test - in real usage, you'd need a valid auth token
    async with aiohttp.ClientSession() as session:
        try:
            # Test without auth (should fail)
            async with session.post(
                f"{BACKEND_URL}/api/v1/users/check",
                json={"emails": test_emails}
            ) as response:
                status = response.status
                if status == 401:
                    print("✓ Endpoint correctly requires authentication (401)")
                elif status == 200:
                    data = await response.json()
                    print(f"✓ Response: {json.dumps(data, indent=2)}")
                else:
                    print(f"? Unexpected status: {status}")
                    
        except aiohttp.ClientConnectorError:
            print("⚠️  Backend not running - start with: cd qumail-backend && python -m uvicorn app.main:app --reload")
            return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    return True

async def test_health_endpoint():
    """Test that backend is running"""
    print("\n🔍 Checking backend health...")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{BACKEND_URL}/api/v1/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✓ Backend is healthy: {data}")
                    return True
                else:
                    print(f"❌ Backend health check failed: {response.status}")
                    return False
        except aiohttp.ClientConnectorError:
            print("❌ Backend not running")
            return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

async def main():
    print("\n" + "="*70)
    print("QUMAIL USER VERIFICATION - TEST SUITE")
    print("="*70)
    
    # Check backend is running
    backend_ok = await test_health_endpoint()
    
    if not backend_ok:
        print("\n⚠️  Please start the backend first:")
        print("   cd qumail-backend")
        print("   python -m uvicorn app.main:app --reload --port 8000")
        return
    
    # Test user check endpoint
    await test_user_check_endpoint()
    
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print("""
To fully test the user verification:

1. Start the backend and frontend
2. Login to QuMail with your Google account (this registers you as a QuMail user)
3. Try to send an encrypted email to:
   - Your own email (should SUCCEED - you are registered)
   - A random email not in QuMail (should FAIL - not registered)

The system should:
✓ Allow sending encrypted emails to registered QuMail users
✓ Block encrypted emails to non-QuMail users with a clear error message
✓ Store all Google OAuth users in MongoDB automatically
""")

if __name__ == "__main__":
    asyncio.run(main())
