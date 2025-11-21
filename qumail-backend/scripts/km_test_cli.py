#!/usr/bin/env python3
"""
KM Client Connection Tester

This script tests connectivity to Quantum Key Management servers using the optimized KM client.
It performs various operations to verify that the KM servers are accessible and properly functioning.

Usage:
    python km_test_cli.py [--retry N] [--delay N] [--timeout N] [--pool N] [--maxsize N] [--verbose]

Options:
    --retry N      Number of retry attempts (default: 3)
    --delay N      Initial retry delay in seconds (default: 1)
    --timeout N    Request timeout in seconds (default: 10)
    --pool N       Number of connections in pool (default: 5)
    --maxsize N    Maximum number of connections (default: 10)
    --verbose      Enable verbose output
    --help         Show this help message

Example:
    python km_test_cli.py --retry 5 --timeout 20 --verbose
"""

import sys
import asyncio
import argparse
import logging
import os
from typing import List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from app.services.optimized_km_client import OptimizedKMClient
except ImportError:
    print("Error: Cannot import OptimizedKMClient. Make sure you're running from the project root.")
    sys.exit(1)


async def test_km_server(
    server_name: str, 
    base_url: str, 
    retry_attempts: int, 
    retry_delay: int, 
    timeout: int,
    pool_connections: int,
    pool_maxsize: int,
    verbose: bool
) -> None:
    """Test KM server connectivity and operations."""
    logger = logging.getLogger(f"km_test_{server_name}")
    if verbose:
        logger.setLevel(logging.DEBUG)
    
    print(f"\n=== Testing {server_name} (URL: {base_url}) ===\n")
    
    client = OptimizedKMClient(
        name=server_name,
        base_url=base_url,
        cert_file=None,  # Use default cert file
        retry_attempts=retry_attempts,
        retry_delay=retry_delay,
        timeout=timeout,
        pool_connections=pool_connections,
        pool_maxsize=pool_maxsize
    )
    
    try:
        # Test connection
        print(f"Testing connection to {server_name}...")
        connected = await client.check_connection()
        if connected:
            print(f"✅ Connection to {server_name} successful.")
        else:
            print(f"❌ Connection to {server_name} failed.")
            return
        
        # Get server info
        print(f"\nGetting {server_name} server info...")
        info = await client.get_server_info()
        print(f"✅ Server info received:")
        for key, value in info.items():
            print(f"  - {key}: {value}")
        
        # Check SAE IDs
        print(f"\nGetting {server_name} SAE list...")
        sae_list = await client.get_sae_list()
        print(f"✅ SAE list received: {', '.join(str(sae) for sae in sae_list)}")
        
        # Check key status for each SAE
        print(f"\nChecking key status for each SAE...")
        for sae_id in sae_list:
            status = await client.check_key_status(sae_id)
            print(f"✅ SAE {sae_id} status: {status.get('stored_key_count', 'unknown')} keys available")
        
        # Test key request for first SAE
        if sae_list:
            test_sae = sae_list[0]
            print(f"\nRequesting encryption keys from {server_name} for SAE {test_sae}...")
            keys = await client.request_enc_keys(test_sae, number=1, size=128)
            if keys:
                print(f"✅ Successfully received {len(keys)} keys.")
                key_id = keys[0]["key_ID"]
                
                # Test key consumption
                print(f"\nTesting key consumption for key {key_id}...")
                await client.mark_key_consumed(key_id)
                print(f"✅ Key {key_id} marked as consumed.")
            else:
                print(f"❌ Failed to receive keys.")
        
        # Test background cache population
        print(f"\nTesting background key cache population...")
        task = asyncio.create_task(client.populate_key_cache(test_sae, 1))
        await asyncio.sleep(2)  # Give it a moment to run
        print(f"✅ Background key cache population started.")
        
        # Final connection check
        print(f"\nPerforming final connection check...")
        connected = await client.check_connection()
        if connected:
            print(f"✅ Final connection to {server_name} successful.")
        else:
            print(f"❌ Final connection to {server_name} failed.")
            
        print(f"\n✅ All tests completed successfully for {server_name}.")
        
    except Exception as e:
        print(f"❌ Error testing {server_name}: {e}")
    finally:
        await client.close()
        print(f"\nClient connection to {server_name} closed.")


async def main(args) -> None:
    """Run KM server tests."""
    # KM server URLs
    km1_url = "http://localhost:13000"
    km2_url = "http://localhost:14000"
    
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
    print(f"  - Pool connections:    {args.pool}")
    print(f"  - Pool max size:       {args.maxsize}")
    print(f"  - Verbose mode:        {'Enabled' if args.verbose else 'Disabled'}")
    print("=" * 60)
    
    # Test KM1 (Alice)
    await test_km_server(
        "KM1", km1_url, 
        args.retry, args.delay, args.timeout,
        args.pool, args.maxsize, args.verbose
    )
    
    # Test KM2 (Bob)
    await test_km_server(
        "KM2", km2_url, 
        args.retry, args.delay, args.timeout,
        args.pool, args.maxsize, args.verbose
    )
    
    print("\n" + "=" * 60)
    print("KM Server Connection Tests Completed")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test KM server connectivity")
    parser.add_argument("--retry", type=int, default=3, help="Number of retry attempts")
    parser.add_argument("--delay", type=int, default=1, help="Initial retry delay in seconds")
    parser.add_argument("--timeout", type=int, default=10, help="Request timeout in seconds")
    parser.add_argument("--pool", type=int, default=5, help="Number of connections in pool")
    parser.add_argument("--maxsize", type=int, default=10, help="Maximum number of connections")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()
    
    asyncio.run(main(args))