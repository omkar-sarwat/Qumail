"""
Test script for quantum KME integration
This script checks the connection between the QuMail backend and the QKD KME server
"""
import asyncio
import json
import sys
import os
import httpx
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('quantum_test.log')
    ]
)
logger = logging.getLogger(__name__)

# Set paths
qkd_base_path = Path(r"D:\New folder (8)\qumail-secure-email\qkd_kme_server-master")
qumail_backend_url = "http://localhost:8001"

# We'll use real authentication by logging in first
SESSION_TOKEN = None

async def start_kme_server(kme_config_file):
    """Start a KME server process"""
    import subprocess
    
    try:
        # Check if the config file exists
        config_path = qkd_base_path / kme_config_file
        if not config_path.exists():
            logger.error(f"Config file not found: {config_path}")
            return None
        
        # Start the KME server - use the actual path found in the workspace
        # Check multiple possible locations and executable names
        possible_paths = [
            qkd_base_path / "target" / "release" / "qkd_kme_server",
            qkd_base_path / "target" / "release" / "qkd_kme_server.exe",
            qkd_base_path / "target" / "debug" / "qkd_kme_server",
            qkd_base_path / "target" / "debug" / "qkd_kme_server.exe"
        ]
        
        exe_path = None
        for path in possible_paths:
            if os.path.exists(path):
                # Use relative path from qkd_base_path
                exe_path = str(path.relative_to(qkd_base_path))
                logger.info(f"Found KME server executable at: {path}")
                break
                
        if not exe_path:
            # Log more detailed error information
            logger.error(f"Could not find KME server executable in {qkd_base_path}")
            logger.error("Searched the following paths:")
            for path in possible_paths:
                logger.error(f" - {path} (exists: {os.path.exists(path)})")
            return None
            
        # Use PowerShell-compatible command for Windows
        # Convert path objects to strings with proper escaping
        base_path_str = str(qkd_base_path).replace('\\', '/')
        config_str = str(kme_config_file)
        exe_path_str = exe_path.replace('\\', '/')
        
        cmd = f"Set-Location -Path '{base_path_str}'; & './{exe_path_str}' '{config_str}'"
        logger.debug(f"PowerShell command: {cmd}")
        
        logger.info(f"Starting KME server with command: {cmd}")
        
        # Use Popen to start detached process
        process = subprocess.Popen(
            ["powershell", "-Command", cmd], 
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Give it a moment to start
        await asyncio.sleep(2)
        
        # Check if process started successfully
        if process.poll() is not None:
            stderr = process.stderr.read()
            logger.error(f"Failed to start KME server: {stderr}")
            return None
        
        logger.info(f"KME server started with PID: {process.pid}")
        return process
        
    except Exception as e:
        logger.error(f"Error starting KME server: {e}")
        return None

async def check_backend_status():
    """Check if the QuMail backend is running"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{qumail_backend_url}/health", timeout=5.0)
            
            if response.status_code != 200:
                logger.error(f"Backend health check failed: {response.status_code}")
                return False
                
            logger.info("Backend is running")
            return True
            
    except Exception as e:
        logger.error(f"Backend health check failed: {e}")
        return False
        
async def perform_real_login():
    """Perform real login to get a session token"""
    global SESSION_TOKEN
    
    try:
        logger.info("Authenticating with the backend...")
        
        # This is where you'd typically make a real login request
        # For testing purposes, we'll directly use a session token
        # that was previously obtained through normal login process
        
        # In a real implementation, you might do something like this:
        # 1. Get a list of users from the database
        # 2. Use the credentials of a test user to log in
        # 3. Save the session token
        
        # For now, we'll query the most recent user in the database
        async with httpx.AsyncClient() as client:
            # Get user profile of most recently logged in user
            response = await client.get(f"{qumail_backend_url}/api/v1/auth/profile")
            
            if response.status_code == 200:
                # Got an existing user profile, we can use this session
                profile = response.json()
                logger.info(f"Using existing session for user: {profile['email']}")
                
                # The session cookie should be in the response cookies
                cookies = response.cookies
                if "session_token" in cookies:
                    SESSION_TOKEN = cookies["session_token"]
                    logger.info("Successfully obtained session token from cookies")
                    return True
                else:
                    logger.warning("No session token found in cookies")
            else:
                logger.warning(f"Failed to get user profile: {response.status_code}")
                
            # If we couldn't get a profile, try to get the user directly
            # This would require either:
            # 1. Having a test user with known credentials
            # 2. Creating a special endpoint for testing
            
            # For now, fail and require manual login
            logger.error("Could not obtain a session token. Please log in manually first.")
            return False
            
    except Exception as e:
        logger.error(f"Real login failed: {e}")
        return False

async def test_quantum_status():
    """Test the quantum status endpoint"""
    try:
        headers = {"Authorization": f"Bearer {SESSION_TOKEN}"}
        logger.info("Testing quantum status endpoint with session token")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{qumail_backend_url}/api/v1/quantum/status",
                    headers=headers,
                    timeout=10.0  # Increase timeout for potentially slow response
                )
                
                logger.debug(f"Response headers: {response.headers}")
                logger.debug(f"Response status: {response.status_code}")
                
                if response.status_code != 200:
                    logger.error(f"Quantum status check failed with status code: {response.status_code}")
                    logger.error(f"Response body: {response.text}")
                    
                    # Check specific error cases
                    if response.status_code == 401:
                        logger.error("Authentication failed. Check the TEST_API_KEY value.")
                    elif response.status_code == 404:
                        logger.error("Endpoint not found. Check if the quantum routes are registered correctly.")
                    elif response.status_code >= 500:
                        logger.error("Server error. Check the backend logs for details.")
                        
                    return False
                    
                status = response.json()
                logger.info(f"Quantum status: {json.dumps(status, indent=2)}")
                
                # Check if status response has the expected structure
                if "servers" not in status and "kme_servers" not in status:
                    logger.warning("Unexpected response format - no servers field found")
                    logger.debug(f"Response keys: {list(status.keys())}")
                    
                # Try both possible field names for servers
                servers = status.get("servers", status.get("kme_servers", []))
                online_servers = [s for s in servers if s.get("status") == "online" or s.get("status") == "connected"]
                
                if not online_servers:
                    logger.warning("No online KME servers found")
                    return False
                    
                logger.info(f"Found {len(online_servers)} online KME servers")
                return True
                
            except httpx.RequestError as e:
                logger.error(f"Request error during quantum status check: {e}")
                return False
                
    except Exception as e:
        logger.error(f"Quantum status test failed with exception: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

async def test_key_exchange():
    """Test the quantum key exchange endpoint"""
    try:
        headers = {"Authorization": f"Bearer {SESSION_TOKEN}"}
        logger.info("Testing key exchange with session token")
        
        data = {
            "sender_kme_id": 1,
            "recipient_kme_id": 2
        }
        
        logger.debug(f"Key exchange request data: {json.dumps(data)}")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{qumail_backend_url}/api/v1/quantum/key/exchange",
                    json=data,
                    headers=headers,
                    timeout=15.0  # Increase timeout for key exchange
                )
                
                logger.debug(f"Response headers: {response.headers}")
                logger.debug(f"Response status: {response.status_code}")
                
                if response.status_code != 200:
                    logger.error(f"Key exchange failed with status code: {response.status_code}")
                    logger.error(f"Response body: {response.text}")
                    
                    # Check specific error cases
                    if response.status_code == 401:
                        logger.error("Authentication failed for key exchange. Check the TEST_API_KEY value.")
                    elif response.status_code == 404:
                        logger.error("Key exchange endpoint not found. Check if the quantum routes are registered correctly.")
                    elif response.status_code >= 500:
                        logger.error("Server error during key exchange. Check the backend logs for details.")
                        
                    return False
                    
                result = response.json()
                logger.info(f"Key exchange result: {json.dumps(result, indent=2)}")
                
                # Accept both "success" status and non-error results (endpoint may return different status formats)
                if (result.get("status") == "success" or "error" not in result) and result.get("key_id"):
                    logger.info(f"Successfully exchanged quantum key: {result.get('key_id')}")
                    return True
                else:
                    error_msg = result.get("error", "Unknown error")
                    logger.warning(f"Key exchange completed but was not successful: {error_msg}")
                    return False
                    
            except httpx.RequestError as e:
                logger.error(f"Request error during key exchange: {e}")
                return False
                
    except Exception as e:
        logger.error(f"Key exchange test failed with exception: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

async def send_test_quantum_email():
    """Send a test quantum email"""
    try:
        headers = {"Authorization": f"Bearer {SESSION_TOKEN}"}
        logger.info("Testing quantum email sending with session token")
        
        async with httpx.AsyncClient() as client:
            try:
                # First get available keys
                logger.info("Checking available quantum keys...")
                keys_response = await client.get(
                    f"{qumail_backend_url}/api/v1/quantum/keys/available", 
                    headers=headers,
                    timeout=10.0
                )
                
                if keys_response.status_code != 200:
                    logger.error(f"Failed to get available keys: Status {keys_response.status_code}")
                    logger.error(f"Response body: {keys_response.text}")
                    return False
                    
                keys_data = keys_response.json()
                logger.debug(f"Available keys response: {json.dumps(keys_data, indent=2)}")
                
                if keys_data.get("count", 0) == 0:
                    logger.warning("No quantum keys available for email. Test will proceed but might fail.")
                else:
                    logger.info(f"Found {keys_data.get('count', 0)} available quantum keys")
                
                # Send test email via /emails/encryption/status endpoint
                logger.info("Checking encryption status...")
                status_response = await client.get(
                    f"{qumail_backend_url}/encryption/status",
                    headers=headers,
                    timeout=10.0
                )
                
                if status_response.status_code != 200:
                    logger.error(f"Failed to get encryption status: Status {status_response.status_code}")
                    logger.error(f"Response body: {status_response.text}")
                    logger.warning("Continuing with email test despite encryption status failure")
                else:
                    status_data = status_response.json()
                    logger.debug(f"Encryption status: {json.dumps(status_data, indent=2)}")
                
                # Prepare and send quantum email using the real email endpoint
                logger.info("Sending test quantum-secured email...")
                email_data = {
                    "recipient": "recipient@example.com",
                    "subject": "Test Quantum Secure Email",
                    "body": "This is a test email encrypted with real quantum keys.",
                    "securityLevel": 2  # Quantum-Enhanced AES
                }
                
                logger.debug(f"Email request data: {json.dumps(email_data, indent=2)}")
                
                email_response = await client.post(
                    f"{qumail_backend_url}/emails/send",
                    json=email_data,
                    headers=headers,
                    timeout=15.0
                )
                
                if email_response.status_code != 200:
                    logger.error(f"Failed to send quantum email: Status {email_response.status_code}")
                    logger.error(f"Response body: {email_response.text}")
                    return False
                    
                result = email_response.json()
                logger.info(f"Quantum email sent successfully: {json.dumps(result, indent=2)}")
                return True
                
            except httpx.RequestError as e:
                logger.error(f"Request error during quantum email test: {e}")
                return False
                
    except Exception as e:
        logger.error(f"Send quantum email test failed with exception: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

async def test_authentication():
    """Test real authentication using session token"""
    global SESSION_TOKEN
    
    if not SESSION_TOKEN:
        logger.error("No session token available. Please log in first.")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {SESSION_TOKEN}"}
        logger.info("Testing authentication with session token")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{qumail_backend_url}/api/v1/auth/me",
                headers=headers
            )
            
            if response.status_code != 200:
                logger.error(f"Authentication failed: {response.status_code} {response.text}")
                return False
                
            auth_data = response.json()
            logger.info(f"Authentication successful for user: {auth_data['email']}")
            return True
            
    except Exception as e:
        logger.error(f"Authentication test failed: {e}")
        return False

async def run_tests():
    """Run all tests in sequence"""
    logger.info("Starting quantum integration tests")
    
    # Check if backend is running
    if not await check_backend_status():
        logger.error("Backend not running. Please start the QuMail backend first.")
        return
        
    # Perform real login first
    logger.info("\n=== Performing Real Authentication ===")
    login_ok = await perform_real_login()
    if not login_ok:
        logger.error("Real login failed. Cannot proceed with tests.")
        return
        
    # Test authentication
    logger.info("\n=== Testing Authentication ===")
    auth_ok = await test_authentication()
    if not auth_ok:
        logger.error("Authentication test failed. Cannot proceed with other tests.")
        return
        
    # Test quantum status
    logger.info("\n=== Testing Quantum Status ===")
    status_ok = await test_quantum_status()
    
    if not status_ok:
        logger.warning("Quantum status test failed. Starting KME servers...")
        
        # Try to start KME servers
        kme1_process = await start_kme_server("config_kme1.json5")
        kme2_process = await start_kme_server("config_kme2.json5")
        
        # Wait for servers to initialize
        logger.info("Waiting for KME servers to initialize...")
        await asyncio.sleep(5)
        
        # Try status check again
        status_ok = await test_quantum_status()
        
    # Test key exchange
    logger.info("\n=== Testing Quantum Key Exchange ===")
    key_exchange_ok = await test_key_exchange()
    
    # Test sending quantum email
    logger.info("\n=== Testing Quantum Email Sending ===")
    email_ok = await send_test_quantum_email()
    
    # Report results
    logger.info("\n=== Test Results ===")
    logger.info(f"Quantum Status Test: {'PASSED' if status_ok else 'FAILED'}")
    logger.info(f"Quantum Key Exchange Test: {'PASSED' if key_exchange_ok else 'FAILED'}")
    logger.info(f"Quantum Email Test: {'PASSED' if email_ok else 'FAILED'}")
    
    overall_status = all([status_ok, key_exchange_ok, email_ok])
    logger.info(f"\nOverall Test Result: {'PASSED' if overall_status else 'FAILED'}")

if __name__ == "__main__":
    asyncio.run(run_tests())