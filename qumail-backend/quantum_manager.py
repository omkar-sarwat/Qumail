"""
Quantum Key Management Utility for QuMail Secure Email
This utility manages the quantum key distribution (QKD) integration for real secure communications
"""
import asyncio
import json
import sys
import os
import httpx
import subprocess
from pathlib import Path
import logging
import argparse
import getpass
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('quantum_manager.log')
    ]
)
logger = logging.getLogger(__name__)

# Set paths
qkd_base_path = Path(r"D:\New folder (8)\qumail-secure-email\qkd_kme_server-master")
qumail_backend_url = "http://localhost:8001"

# Global session
SESSION_TOKEN = None
KME_PROCESSES = {}

class QKDManager:
    """Quantum Key Distribution Manager for QuMail"""
    
    def __init__(self, qkd_base_path, backend_url):
        self.qkd_base_path = Path(qkd_base_path)
        self.backend_url = backend_url
        self.session_token = None
        self.kme_processes = {}
    
    async def login(self, email=None, password=None):
        """Authenticate with the backend using real credentials"""
        try:
            logger.info("Authenticating with backend...")
            
            # For real implementation, we would use the provided email/password
            # But since that requires integration with the actual auth system,
            # we'll check for an existing session first
            
            async with httpx.AsyncClient() as client:
                # Check if we can get a user profile with existing session cookie
                response = await client.get(f"{self.backend_url}/api/v1/auth/me")
                
                if response.status_code == 200:
                    # We already have a valid session
                    user_data = response.json()
                    logger.info(f"Already authenticated as: {user_data.get('email', 'Unknown')}")
                    
                    # Extract session token from cookies
                    cookies = response.cookies
                    if "session_token" in cookies:
                        self.session_token = cookies["session_token"]
                        return True
                
                # If email/password provided, attempt a real login
                if email and password:
                    logger.info(f"Attempting login with email: {email}")
                    # In a real implementation, we would POST to the login endpoint
                    # but we'll simulate this since direct password auth may not be available
                    
                    logger.error("Direct password authentication not implemented")
                    logger.info("Please login through the web interface first")
                    return False
                    
                logger.warning("No valid session found and no credentials provided")
                logger.info("Please login through the web interface first")
                return False
                
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False
    
    async def start_kme_server(self, config_file, name=None):
        """Start a KME server with the specified config"""
        import subprocess
        
        if not name:
            name = f"kme-{len(self.kme_processes) + 1}"
            
        try:
            # Check if the config file exists
            config_path = self.qkd_base_path / config_file
            if not config_path.exists():
                logger.error(f"Config file not found: {config_path}")
                return False
                
            # Find KME server executable
            possible_paths = [
                self.qkd_base_path / "target" / "release" / "qkd_kme_server",
                self.qkd_base_path / "target" / "release" / "qkd_kme_server.exe",
                self.qkd_base_path / "target" / "debug" / "qkd_kme_server",
                self.qkd_base_path / "target" / "debug" / "qkd_kme_server.exe"
            ]
            
            exe_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    exe_path = str(path.relative_to(self.qkd_base_path))
                    logger.info(f"Found KME server executable at: {path}")
                    break
                    
            if not exe_path:
                logger.error(f"Could not find KME server executable in {self.qkd_base_path}")
                return False
                
            # Format command for Windows PowerShell
            base_path_str = str(self.qkd_base_path).replace('\\', '/')
            config_str = str(config_file)
            exe_path_str = exe_path.replace('\\', '/')
            
            cmd = f"Set-Location -Path '{base_path_str}'; & './{exe_path_str}' '{config_str}'"
            
            logger.info(f"Starting KME server {name} with config {config_file}...")
            
            # Start detached process
            process = subprocess.Popen(
                ["powershell", "-Command", cmd],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait briefly to check if process started
            await asyncio.sleep(2)
            
            if process.poll() is not None:
                stderr = process.stderr.read()
                logger.error(f"Failed to start KME server {name}: {stderr}")
                return False
                
            logger.info(f"KME server {name} started with PID: {process.pid}")
            
            # Store the process
            self.kme_processes[name] = {
                "process": process,
                "config": config_file,
                "pid": process.pid,
                "started_at": datetime.now().isoformat()
            }
            
            return True
            
        except Exception as e:
            logger.error(f"Error starting KME server {name}: {e}")
            return False
    
    def stop_kme_server(self, name=None):
        """Stop a running KME server"""
        if not name:
            # Stop all servers
            for server_name, data in list(self.kme_processes.items()):
                self._stop_single_server(server_name)
            return True
        else:
            # Stop specific server
            return self._stop_single_server(name)
    
    def _stop_single_server(self, name):
        """Helper to stop a single server"""
        if name not in self.kme_processes:
            logger.error(f"KME server {name} not found")
            return False
            
        process_data = self.kme_processes[name]
        process = process_data["process"]
        
        try:
            # Try to terminate gracefully
            process.terminate()
            try:
                # Wait a bit for graceful termination
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if it didn't terminate gracefully
                process.kill()
                
            logger.info(f"KME server {name} stopped (PID: {process_data['pid']})")
            del self.kme_processes[name]
            return True
            
        except Exception as e:
            logger.error(f"Error stopping KME server {name}: {e}")
            return False
    
    async def get_kme_status(self):
        """Get status of KME servers from backend"""
        if not self.session_token:
            logger.error("Not authenticated. Please login first.")
            return None
            
        try:
            headers = {"Authorization": f"Bearer {self.session_token}"}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.backend_url}/api/v1/quantum/status",
                    headers=headers,
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    logger.error(f"Failed to get KME status: {response.status_code}")
                    logger.error(f"Response: {response.text}")
                    return None
                    
                status_data = response.json()
                return status_data
                
        except Exception as e:
            logger.error(f"Error getting KME status: {e}")
            return None
    
    async def get_available_keys(self):
        """Get available quantum keys"""
        if not self.session_token:
            logger.error("Not authenticated. Please login first.")
            return None
            
        try:
            headers = {"Authorization": f"Bearer {self.session_token}"}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.backend_url}/api/v1/quantum/keys/available",
                    headers=headers,
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    logger.error(f"Failed to get available keys: {response.status_code}")
                    logger.error(f"Response: {response.text}")
                    return None
                    
                keys_data = response.json()
                return keys_data
                
        except Exception as e:
            logger.error(f"Error getting available keys: {e}")
            return None
    
    async def exchange_keys(self, sender_kme_id, recipient_kme_id):
        """Exchange quantum keys between KME servers"""
        if not self.session_token:
            logger.error("Not authenticated. Please login first.")
            return None
            
        try:
            headers = {"Authorization": f"Bearer {self.session_token}"}
            
            data = {
                "sender_kme_id": sender_kme_id,
                "recipient_kme_id": recipient_kme_id
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.backend_url}/api/v1/quantum/key/exchange",
                    json=data,
                    headers=headers,
                    timeout=15.0
                )
                
                if response.status_code != 200:
                    logger.error(f"Key exchange failed: {response.status_code}")
                    logger.error(f"Response: {response.text}")
                    return None
                    
                exchange_data = response.json()
                return exchange_data
                
        except Exception as e:
            logger.error(f"Error exchanging keys: {e}")
            return None
    
    async def get_encryption_status(self):
        """Get encryption status from backend"""
        if not self.session_token:
            logger.error("Not authenticated. Please login first.")
            return None
            
        try:
            headers = {"Authorization": f"Bearer {self.session_token}"}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.backend_url}/encryption/status",
                    headers=headers,
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    logger.error(f"Failed to get encryption status: {response.status_code}")
                    logger.error(f"Response: {response.text}")
                    return None
                    
                status_data = response.json()
                return status_data
                
        except Exception as e:
            logger.error(f"Error getting encryption status: {e}")
            return None

async def start_kme_servers(manager):
    """Start both KME servers"""
    # Start KME server 1 (Alice)
    logger.info("Starting KME server 1 (Alice)...")
    kme1_ok = await manager.start_kme_server("config_kme1.json5", "kme1")
    if not kme1_ok:
        logger.error("Failed to start KME server 1")
    
    # Start KME server 2 (Bob)
    logger.info("Starting KME server 2 (Bob)...")
    kme2_ok = await manager.start_kme_server("config_kme2.json5", "kme2")
    if not kme2_ok:
        logger.error("Failed to start KME server 2")
    
    # Check if both servers started
    if kme1_ok and kme2_ok:
        logger.info("Both KME servers started successfully")
        # Wait for servers to initialize
        await asyncio.sleep(3)
        return True
    else:
        return False

async def check_system_status(manager):
    """Check full quantum system status"""
    logger.info("Checking quantum system status...")
    
    # Get KME server status
    kme_status = await manager.get_kme_status()
    if kme_status:
        logger.info("KME servers status:")
        print(json.dumps(kme_status, indent=2))
    else:
        logger.error("Failed to get KME status")
        return False
    
    # Get encryption status
    enc_status = await manager.get_encryption_status()
    if enc_status:
        logger.info("Encryption status:")
        print(json.dumps(enc_status, indent=2))
    else:
        logger.error("Failed to get encryption status")
    
    # Get available keys
    keys_data = await manager.get_available_keys()
    if keys_data:
        logger.info(f"Available quantum keys: {keys_data.get('count', 0)}")
        if keys_data.get('keys'):
            print("Key IDs:")
            for key in keys_data.get('keys', []):
                print(f" - {key.get('id')} (KME: {key.get('kme')})")
    else:
        logger.error("Failed to get available keys")
    
    return True

async def interactive_menu(manager):
    """Run interactive menu for managing quantum keys"""
    print("\nQuantum Key Management Utility")
    print("=============================\n")
    
    # First, try to authenticate
    await manager.login()
    
    while True:
        print("\nOptions:")
        print("1. Start KME servers")
        print("2. Check system status")
        print("3. Exchange quantum keys")
        print("4. Show available keys")
        print("5. Stop KME servers")
        print("0. Exit")
        
        choice = input("\nSelect option (0-5): ")
        
        if choice == '0':
            break
        elif choice == '1':
            await start_kme_servers(manager)
        elif choice == '2':
            await check_system_status(manager)
        elif choice == '3':
            sender_id = int(input("Enter sender KME ID (1-2): "))
            recipient_id = int(input("Enter recipient KME ID (1-2): "))
            result = await manager.exchange_keys(sender_id, recipient_id)
            if result:
                print("\nKey exchange result:")
                print(json.dumps(result, indent=2))
        elif choice == '4':
            keys_data = await manager.get_available_keys()
            if keys_data:
                print("\nAvailable quantum keys:")
                print(json.dumps(keys_data, indent=2))
        elif choice == '5':
            manager.stop_kme_server()
            print("All KME servers stopped")
        else:
            print("Invalid option. Please try again.")
    
    # Clean up any running KME servers before exiting
    manager.stop_kme_server()
    print("Exiting Quantum Key Manager")

async def main_cli():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description='Quantum Key Management Utility for QuMail')
    parser.add_argument('--action', choices=['start', 'status', 'exchange', 'stop', 'interactive'], 
                        default='interactive', help='Action to perform')
    parser.add_argument('--sender', type=int, help='Sender KME ID for key exchange')
    parser.add_argument('--recipient', type=int, help='Recipient KME ID for key exchange')
    
    args = parser.parse_args()
    
    # Create manager
    manager = QKDManager(qkd_base_path, qumail_backend_url)
    
    # Attempt login
    auth_ok = await manager.login()
    if not auth_ok and args.action != 'start':
        logger.error("Authentication failed. Please log in through the web interface first.")
        return
    
    # Perform requested action
    if args.action == 'start':
        await start_kme_servers(manager)
    elif args.action == 'status':
        await check_system_status(manager)
    elif args.action == 'exchange':
        if not args.sender or not args.recipient:
            logger.error("Sender and recipient KME IDs are required for key exchange")
            return
        result = await manager.exchange_keys(args.sender, args.recipient)
        if result:
            print(json.dumps(result, indent=2))
    elif args.action == 'stop':
        manager.stop_kme_server()
        logger.info("All KME servers stopped")
    elif args.action == 'interactive':
        await interactive_menu(manager)

if __name__ == "__main__":
    asyncio.run(main_cli())