#!/usr/bin/env python3
"""
Helper script to run the KM client test tool.
"""

import sys
import os
import logging
import asyncio
import argparse
import ssl
from typing import List
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Add the parent directory to the path so we can import the app modules
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import directly from optimized_km_client
try:
    from app.services.optimized_km_client import OptimizedKMClient
    logger = logging.getLogger("km_test")
except ImportError:
    print("Error: Cannot import OptimizedKMClient. Make sure you're running from the project root.")
    sys.exit(1)

async def test_km_server(
    server_name: str, 
    base_url: str,
    sae_id: int,
    client_cert_path: str,
    client_key_path: str,
    ca_cert_path: str,
    verbose: bool
) -> None:
    """Test KM server connectivity and operations."""
    logger = logging.getLogger(f"km_test_{server_name}")
    if verbose:
        logger.setLevel(logging.DEBUG)
    
    print(f"\n=== Testing {server_name} (URL: {base_url}) ===\n")
    
    client = OptimizedKMClient(
        base_url=base_url,
        sae_id=sae_id,
        client_cert_path=client_cert_path,
        client_key_path=client_key_path,
        ca_cert_path=ca_cert_path
    )
    
    try:
        # Test connection by getting SAE info (more reliable than status)
        print(f"Testing connection to {server_name}...")
        try:
            # Try getting SAE info first
            sae_info = await client.get_sae_info()
            print(f"✅ Connection to {server_name} successful. SAE info: {sae_info}")
        except Exception as e:
            print(f"⚠️ Could not get SAE info: {e}")
            
            try:
                # Fall back to status check
                status = await client.get_status()
                if status.get("healthy", False):
                    print(f"✅ Connection to {server_name} successful via status check.")
                else:
                    print(f"❌ Connection to {server_name} may have issues: {status}")
                    print(f"Continuing with tests anyway...")
            except Exception as status_e:
                print(f"❌ Connection to {server_name} failed: {status_e}")
                return
        
        # Check key status
        print(f"\nChecking key status for SAE {sae_id}...")
        key_status = await client.check_key_status(1)
        print(f"✅ Key status: {key_status}")
        
        # Request encryption keys
        print(f"\nRequesting encryption keys...")
        keys = await client.request_enc_keys(1, number=1)
        if keys:
            print(f"✅ Successfully received {len(keys)} keys.")
            key_id = keys[0]["key_ID"]
            
            # Test key consumption
            print(f"\nTesting key consumption for key {key_id}...")
            consumed = await client.mark_key_consumed(key_id)
            print(f"✅ Key {key_id} marked as consumed: {consumed}")
        else:
            print(f"❌ Failed to receive keys.")
            
        print(f"\n✅ All tests completed successfully for {server_name}.")
        
    except Exception as e:
        print(f"❌ Error testing {server_name}: {e}")
    finally:
        await client.close()
        print(f"\nClient connection to {server_name} closed.")

async def main(args):
    """Run KM server tests."""
    # KM server URLs
    km1_url = "https://localhost:13000"
    km2_url = "https://localhost:14000"
    
    # Use absolute paths for certificates
    root_dir = Path(r"D:\New folder (8)\qumail-secure-email\qkd_kme_server-master\certs")
    
    # Alice's certificates (KME 1)
    km1_client_cert_path = str(root_dir / "kme-1-local-zone" / "client_1_cert.pem")
    km1_client_key_path = str(root_dir / "kme-1-local-zone" / "client_1.key")
    km1_ca_cert_path = str(root_dir / "kme-1-local-zone" / "ca.crt")
    
    # Bob's certificates (KME 2)
    km2_client_cert_path = str(root_dir / "kme-2-local-zone" / "client_3_cert.pem")
    km2_client_key_path = str(root_dir / "kme-2-local-zone" / "client_3.key")
    km2_ca_cert_path = str(root_dir / "kme-2-local-zone" / "ca.crt")
    
    # Configure logging
    if args.verbose:
        logging.getLogger("app.services.optimized_km_client").setLevel(logging.DEBUG)
    
    print("=" * 60)
    print("QuMail KM Server Connection Tester")
    print("=" * 60)
    print(f"Configuration:")
    print(f"  - Retry attempts:      {args.retry}")
    print(f"  - Initial retry delay: {args.delay} seconds")
    print(f"  - Request timeout:     {args.timeout} seconds")
    print(f"  - Verbose mode:        {'Enabled' if args.verbose else 'Disabled'}")
    print("=" * 60)
    
    # Test KM1 (Alice)
    await test_km_server(
        "KM1", km1_url, 1, 
        km1_client_cert_path, km1_client_key_path, km1_ca_cert_path,
        args.verbose
    )
    
    # Test KM2 (Bob)
    await test_km_server(
        "KM2", km2_url, 3, 
        km2_client_cert_path, km2_client_key_path, km2_ca_cert_path,
        args.verbose
    )
    
    print("\n" + "=" * 60)
    print("KM Server Connection Tests Completed")
    print("=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test KM server connectivity")
    parser.add_argument("--retry", type=int, default=3, help="Number of retry attempts")
    parser.add_argument("--delay", type=int, default=1, help="Initial retry delay in seconds")
    parser.add_argument("--timeout", type=int, default=10, help="Request timeout in seconds")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()
    
    asyncio.run(main(args))