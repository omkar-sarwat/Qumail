#!/usr/bin/env python
"""
QKD KME Connectivity Test Script

This script tests connectivity to the QKD Key Management Entity (KME) servers
configured in the QuMail system. It checks various endpoints and operations
to verify that the KME servers are functioning correctly.

Usage:
    python test_qkd_connectivity.py [--kme KME_ID] [--verbose]

Arguments:
    --kme KME_ID      Test only the specified KME ID (1 or 2)
    --verbose         Show detailed output for each test

Example:
    python test_qkd_connectivity.py --kme 1 --verbose
"""

import os
import sys
import asyncio
import argparse
import logging
import json
import ssl
import base64
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import aiohttp
from cryptography import x509
from cryptography.hazmat.backends import default_backend

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("qkd_connectivity_test")

# Get the absolute path to the project root
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

class KmeConnectionTester:
    """Tests connectivity to KME servers"""
    
    def __init__(self, verbose: bool = False):
        """Initialize the KME connection tester"""
        self.verbose = verbose
        if verbose:
            logger.setLevel(logging.DEBUG)
        
        # KME server configuration
        self.kme_servers = [
            {
                "id": 1,
                "name": "KME 1 (Alice)",
                "base_url": "https://localhost:13000",
                "cert_path": os.path.join(PROJECT_ROOT, "certs/kme-1-local-zone/client_1.pfx"), 
                "cert_password": "password",
                "ca_cert_path": os.path.join(PROJECT_ROOT, "certs/kme-1-local-zone/ca.crt")
            },
            {
                "id": 2,
                "name": "KME 2 (Bob)",
                "base_url": "https://localhost:14000",
                "cert_path": os.path.join(PROJECT_ROOT, "certs/kme-2-local-zone/client_3.pfx"),
                "cert_password": "password",
                "ca_cert_path": os.path.join(PROJECT_ROOT, "certs/kme-2-local-zone/ca.crt")
            }
        ]
        
        # Base paths relative to the project root
        self.base_path = Path(PROJECT_ROOT)
        
        # Keep SSL contexts in memory for reuse
        self._ssl_contexts = {}
    
    async def _get_ssl_context(self, server_id: int) -> ssl.SSLContext:
        """
        Get or create an SSL context for a KME server
        Uses client certificate authentication
        """
        if server_id in self._ssl_contexts:
            return self._ssl_contexts[server_id]
        
        # Find server config
        server_config = next((s for s in self.kme_servers if s["id"] == server_id), None)
        if not server_config:
            raise Exception(f"KME server with id {server_id} not found in configuration")
        
        # Create SSL context with client certificate
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        
        # Absolute paths to certificates
        cert_path = self.base_path / server_config["cert_path"]
        ca_cert_path = self.base_path / server_config["ca_cert_path"]
        
        if not cert_path.exists():
            raise Exception(f"Client certificate not found at {cert_path}")
        
        if not ca_cert_path.exists():
            raise Exception(f"CA certificate not found at {ca_cert_path}")
        
        logger.debug(f"Using client certificate: {cert_path}")
        logger.debug(f"Using CA certificate: {ca_cert_path}")
        
        # Load CA certificate for server verification
        context.load_verify_locations(cafile=str(ca_cert_path))
        
        # Load client certificate for authentication
        try:
            context.load_cert_chain(
                certfile=str(cert_path), 
                password=server_config["cert_password"]
            )
        except Exception as e:
            raise Exception(f"Failed to load client certificate: {e}")
        
        # Store for reuse
        self._ssl_contexts[server_id] = context
        return context
    
    async def test_root_endpoint(self, server_id: int) -> Dict[str, Any]:
        """Test connectivity to the root endpoint"""
        server_config = next((s for s in self.kme_servers if s["id"] == server_id), None)
        if not server_config:
            return {"success": False, "error": f"KME server with id {server_id} not found"}
        
        try:
            ssl_context = await self._get_ssl_context(server_id)
            
            url = f"{server_config['base_url']}/"
            
            if self.verbose:
                logger.debug(f"Connecting to root endpoint: {url}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, ssl=ssl_context) as response:
                    status = response.status
                    if self.verbose:
                        logger.debug(f"Root endpoint status: {status}")
                    
                    if status != 200:
                        body = await response.text()
                        return {
                            "success": False, 
                            "status": status,
                            "error": f"Root endpoint returned status {status}: {body[:200]}"
                        }
                    
                    try:
                        data = await response.json()
                        if self.verbose:
                            logger.debug(f"Root endpoint data: {json.dumps(data, indent=2)}")
                        return {"success": True, "status": status, "data": data}
                    except Exception as e:
                        body = await response.text()
                        return {
                            "success": False,
                            "status": status, 
                            "error": f"Failed to parse JSON from response: {e}",
                            "body": body[:200]
                        }
                    
        except aiohttp.ClientError as e:
            return {"success": False, "error": f"Network error: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Error connecting to root endpoint: {str(e)}"}
    
    async def test_status_endpoint(self, server_id: int) -> Dict[str, Any]:
        """Test connectivity to the status endpoint"""
        server_config = next((s for s in self.kme_servers if s["id"] == server_id), None)
        if not server_config:
            return {"success": False, "error": f"KME server with id {server_id} not found"}
        
        try:
            ssl_context = await self._get_ssl_context(server_id)
            
            url = f"{server_config['base_url']}/api/v1/status"
            
            if self.verbose:
                logger.debug(f"Connecting to status endpoint: {url}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, ssl=ssl_context) as response:
                    status = response.status
                    if self.verbose:
                        logger.debug(f"Status endpoint response: {status}")
                    
                    if status != 200:
                        body = await response.text()
                        return {
                            "success": False, 
                            "status": status,
                            "error": f"Status endpoint returned status {status}: {body[:200]}"
                        }
                    
                    try:
                        data = await response.json()
                        if self.verbose:
                            logger.debug(f"Status endpoint data: {json.dumps(data, indent=2)}")
                        return {"success": True, "status": status, "data": data}
                    except Exception as e:
                        body = await response.text()
                        return {
                            "success": False,
                            "status": status, 
                            "error": f"Failed to parse JSON from response: {e}",
                            "body": body[:200]
                        }
                    
        except aiohttp.ClientError as e:
            return {"success": False, "error": f"Network error: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Error connecting to status endpoint: {str(e)}"}
    
    async def test_sae_info(self, server_id: int) -> Dict[str, Any]:
        """Test fetching the SAE information"""
        server_config = next((s for s in self.kme_servers if s["id"] == server_id), None)
        if not server_config:
            return {"success": False, "error": f"KME server with id {server_id} not found"}
        
        try:
            ssl_context = await self._get_ssl_context(server_id)
            
            url = f"{server_config['base_url']}/api/v1/sae/info/me"
            
            if self.verbose:
                logger.debug(f"Connecting to SAE info endpoint: {url}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, ssl=ssl_context) as response:
                    status = response.status
                    if self.verbose:
                        logger.debug(f"SAE info response status: {status}")
                    
                    if status != 200:
                        body = await response.text()
                        return {
                            "success": False, 
                            "status": status,
                            "error": f"SAE info endpoint returned status {status}: {body[:200]}"
                        }
                    
                    try:
                        data = await response.json()
                        if self.verbose:
                            logger.debug(f"SAE info data: {json.dumps(data, indent=2)}")
                        return {"success": True, "status": status, "data": data}
                    except Exception as e:
                        body = await response.text()
                        return {
                            "success": False,
                            "status": status, 
                            "error": f"Failed to parse JSON from response: {e}",
                            "body": body[:200]
                        }
                    
        except aiohttp.ClientError as e:
            return {"success": False, "error": f"Network error: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Error connecting to SAE info endpoint: {str(e)}"}

    async def test_key_status(self, server_id: int, slave_sae_id: int = 2) -> Dict[str, Any]:
        """Test checking the key status"""
        server_config = next((s for s in self.kme_servers if s["id"] == server_id), None)
        if not server_config:
            return {"success": False, "error": f"KME server with id {server_id} not found"}
        
        try:
            ssl_context = await self._get_ssl_context(server_id)
            
            # First try to get SAE ID (if not provided)
            if slave_sae_id is None:
                sae_info_result = await self.test_sae_info(server_id)
                if not sae_info_result["success"]:
                    return {
                        "success": False, 
                        "error": f"Could not determine SAE ID: {sae_info_result.get('error', 'Unknown error')}"
                    }
                
                my_sae_id = sae_info_result["data"].get("SAE_ID")
                if not my_sae_id:
                    return {"success": False, "error": "SAE ID not found in response"}
                
                # Determine slave SAE ID (simple logic for this test)
                slave_sae_id = 2 if my_sae_id == 1 else 1
            
            url = f"{server_config['base_url']}/api/v1/keys/{slave_sae_id}/status"
            
            if self.verbose:
                logger.debug(f"Connecting to key status endpoint: {url}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, ssl=ssl_context) as response:
                    status = response.status
                    if self.verbose:
                        logger.debug(f"Key status response: {status}")
                    
                    if status != 200:
                        body = await response.text()
                        return {
                            "success": False, 
                            "status": status,
                            "error": f"Key status endpoint returned status {status}: {body[:200]}"
                        }
                    
                    try:
                        data = await response.json()
                        if self.verbose:
                            logger.debug(f"Key status data: {json.dumps(data, indent=2)}")
                        return {"success": True, "status": status, "data": data}
                    except Exception as e:
                        body = await response.text()
                        return {
                            "success": False,
                            "status": status, 
                            "error": f"Failed to parse JSON from response: {e}",
                            "body": body[:200]
                        }
                    
        except aiohttp.ClientError as e:
            return {"success": False, "error": f"Network error: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Error connecting to key status endpoint: {str(e)}"}

    async def test_get_encryption_key(self, server_id: int, slave_sae_id: int = 2) -> Dict[str, Any]:
        """Test getting an encryption key"""
        server_config = next((s for s in self.kme_servers if s["id"] == server_id), None)
        if not server_config:
            return {"success": False, "error": f"KME server with id {server_id} not found"}
        
        try:
            ssl_context = await self._get_ssl_context(server_id)
            
            # First try to get SAE ID (if not provided)
            if slave_sae_id is None:
                sae_info_result = await self.test_sae_info(server_id)
                if not sae_info_result["success"]:
                    return {
                        "success": False, 
                        "error": f"Could not determine SAE ID: {sae_info_result.get('error', 'Unknown error')}"
                    }
                
                my_sae_id = sae_info_result["data"].get("SAE_ID")
                if not my_sae_id:
                    return {"success": False, "error": "SAE ID not found in response"}
                
                # Determine slave SAE ID (simple logic for this test)
                slave_sae_id = 2 if my_sae_id == 1 else 1
            
            url = f"{server_config['base_url']}/api/v1/keys/{slave_sae_id}/enc_keys"
            
            if self.verbose:
                logger.debug(f"Connecting to encryption keys endpoint: {url}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, ssl=ssl_context) as response:
                    status = response.status
                    if self.verbose:
                        logger.debug(f"Encryption keys response: {status}")
                    
                    if status != 200:
                        body = await response.text()
                        return {
                            "success": False, 
                            "status": status,
                            "error": f"Encryption keys endpoint returned status {status}: {body[:200]}"
                        }
                    
                    try:
                        data = await response.json()
                        keys = data.get("keys", [])
                        
                        # Redact actual key material in verbose mode
                        if self.verbose and keys:
                            censored_keys = []
                            for key in keys:
                                key_copy = key.copy()
                                if "key" in key_copy:
                                    key_copy["key"] = "***REDACTED***"
                                censored_keys.append(key_copy)
                            logger.debug(f"Encryption keys data: {json.dumps({'keys': censored_keys}, indent=2)}")
                        
                        if not keys:
                            return {
                                "success": False,
                                "status": status,
                                "error": "No keys returned from encryption keys endpoint"
                            }
                        
                        return {"success": True, "status": status, "data": data, "key_count": len(keys)}
                    except Exception as e:
                        body = await response.text()
                        return {
                            "success": False,
                            "status": status, 
                            "error": f"Failed to parse JSON from response: {e}",
                            "body": body[:200]
                        }
                    
        except aiohttp.ClientError as e:
            return {"success": False, "error": f"Network error: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Error connecting to encryption keys endpoint: {str(e)}"}

    async def run_tests(self, kme_id: Optional[int] = None) -> Dict[str, Dict[str, Any]]:
        """Run all tests and return results"""
        results = {}
        
        # Filter servers by ID if specified
        servers = self.kme_servers
        if kme_id is not None:
            servers = [s for s in servers if s["id"] == kme_id]
        
        for server in servers:
            server_id = server["id"]
            server_name = server["name"]
            server_results = {}
            
            print(f"\nTesting KME Server {server_id}: {server_name}\n" + "="*50)
            
            # Test root endpoint
            print(f"\nTesting root endpoint connectivity...")
            root_result = await self.test_root_endpoint(server_id)
            server_results["root_endpoint"] = root_result
            
            if root_result["success"]:
                print(f"✓ Successfully connected to root endpoint")
                if "data" in root_result:
                    healthy = root_result["data"].get("healthy", False)
                    print(f"  Server reports healthy: {healthy}")
            else:
                print(f"✗ Failed to connect to root endpoint: {root_result.get('error', 'Unknown error')}")
            
            # Test status endpoint
            print(f"\nTesting status endpoint...")
            status_result = await self.test_status_endpoint(server_id)
            server_results["status_endpoint"] = status_result
            
            if status_result["success"]:
                print(f"✓ Successfully connected to status endpoint")
            else:
                print(f"✗ Failed to connect to status endpoint: {status_result.get('error', 'Unknown error')}")
            
            # Test SAE info endpoint
            print(f"\nTesting SAE info endpoint...")
            sae_info_result = await self.test_sae_info(server_id)
            server_results["sae_info"] = sae_info_result
            
            if sae_info_result["success"]:
                print(f"✓ Successfully retrieved SAE info")
                sae_id = sae_info_result["data"].get("SAE_ID")
                print(f"  SAE ID: {sae_id}")
            else:
                print(f"✗ Failed to retrieve SAE info: {sae_info_result.get('error', 'Unknown error')}")
            
            # Test key status endpoint
            print(f"\nTesting key status endpoint...")
            key_status_result = await self.test_key_status(server_id)
            server_results["key_status"] = key_status_result
            
            if key_status_result["success"]:
                print(f"✓ Successfully retrieved key status")
                if "data" in key_status_result:
                    key_count = key_status_result["data"].get("stored_key_count", 0)
                    print(f"  Available keys: {key_count}")
            else:
                print(f"✗ Failed to retrieve key status: {key_status_result.get('error', 'Unknown error')}")
            
            # Test get encryption keys endpoint
            print(f"\nTesting encryption keys endpoint...")
            enc_keys_result = await self.test_get_encryption_key(server_id)
            server_results["encryption_keys"] = enc_keys_result
            
            if enc_keys_result["success"]:
                print(f"✓ Successfully retrieved encryption keys")
                if "key_count" in enc_keys_result:
                    print(f"  Retrieved {enc_keys_result['key_count']} keys")
            else:
                print(f"✗ Failed to retrieve encryption keys: {enc_keys_result.get('error', 'Unknown error')}")
            
            # Summarize server test results
            print(f"\nSummary for KME Server {server_id}:")
            success_count = sum(1 for test in server_results.values() if test["success"])
            total_tests = len(server_results)
            print(f"Passed {success_count}/{total_tests} tests")
            
            if success_count == total_tests:
                print(f"✓ All tests passed! KME Server {server_id} appears to be fully functional.")
            elif success_count > 0:
                print(f"⚠ Some tests failed. KME Server {server_id} is partially functional.")
            else:
                print(f"✗ All tests failed! KME Server {server_id} appears to be unreachable or misconfigured.")
            
            results[str(server_id)] = server_results
        
        return results

async def main():
    """Main function to run the tests"""
    parser = argparse.ArgumentParser(description="Test connectivity to QKD KME servers")
    parser.add_argument("--kme", type=int, help="Test only the specified KME ID (1 or 2)")
    parser.add_argument("--verbose", action="store_true", help="Show detailed output for each test")
    args = parser.parse_args()
    
    print("\nQKD KME Connectivity Test")
    print("=======================\n")
    
    tester = KmeConnectionTester(verbose=args.verbose)
    await tester.run_tests(kme_id=args.kme)
    
    print("\nTest complete.")

if __name__ == "__main__":
    asyncio.run(main())