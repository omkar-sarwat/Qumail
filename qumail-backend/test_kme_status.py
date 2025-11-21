#!/usr/bin/env python
"""
Test KME Server Integration

This script tests the integration between QuMail and a real ETSI QKD KME server.
It tries to connect to the KME server and retrieve quantum keys.

Usage:
    python test_kme_status.py [--verbose]
"""

import os
import sys
import asyncio
import logging
import argparse
import json
from pathlib import Path

# Import the KME service
from app.services.kme_service import kme_service
from app.services.optimized_km_client import OptimizedKMClient

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("kme_status_test")

async def test_kme_status():
    """Original test function for backward compatibility"""
    try:
        print("Testing get_kme_status function...")
        result = await kme_service.get_kme_status()
        print("KME Status:", result)
    except Exception as e:
        print(f"Error: {e}")

async def test_kme_service():
    """Test KME service connectivity and operations"""
    print("\n=== Testing KME Service ===\n")
    
    try:
        # Get system status
        print("Getting system status...")
        status = await kme_service.get_system_status()
        print(f"System status: {status['system_status']}")
        print(f"Healthy servers: {status['healthy_servers']}/{status['total_servers']}")
        print(f"Total available keys: {status['total_available_keys']}")
        print(f"Average entropy: {status['average_entropy']:.3f}")
        
        # Print server details
        print("\nServer details:")
        for server in status['servers']:
            print(f"  - Server {server['id']} ({server['name']}):")
            print(f"    Status: {server['status']}")
            print(f"    Available keys: {server.get('available_keys', 0)}")
            print(f"    Entropy: {server.get('entropy', 0):.3f}")
            if server['status'] == 'error' and 'message' in server:
                print(f"    Error: {server['message']}")
        
        # Try to get KME status
        print("\nTesting get_kme_status function...")
        result = await kme_service.get_kme_status()
        print(f"KME Status system state: {result['systemStatus']}")
        print(f"Average entropy: {result['averageEntropy']}")
        print(f"Entropy status: {result['entropyStatus']}")
        
        # Try to exchange a quantum key
        if status['healthy_servers'] >= 2:
            print("\nTrying to exchange a quantum key...")
            
            # Get the first two healthy servers
            healthy_servers = [s['id'] for s in status['servers'] if s['status'] == 'online']
            if len(healthy_servers) >= 2:
                sender_id = healthy_servers[0]
                recipient_id = healthy_servers[1]
                
                try:
                    key_id, key_bytes = await kme_service.exchange_quantum_key(sender_id, recipient_id)
                    print(f"Successfully exchanged key: {key_id}")
                    print(f"Key size: {len(key_bytes)} bytes")
                    print(f"Key preview (first 8 bytes): {key_bytes[:8].hex()}")
                except Exception as e:
                    print(f"Failed to exchange key: {e}")
            else:
                print("Not enough healthy servers to exchange keys")
        
    except Exception as e:
        print(f"Error testing KME service: {e}")

async def test_optimized_km_client():
    """Test the OptimizedKMClient"""
    print("\n=== Testing Optimized KM Client ===\n")
    
    try:
        # Create OptimizedKMClient for KME 1
        print("Creating OptimizedKMClient for KME 1...")
        kme1_client = OptimizedKMClient(
            base_url="https://localhost:13000",
            cert_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), "certs/kme-1-local-zone/client_1.pfx"),
            cert_password="password",
            ca_cert_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), "certs/kme-1-local-zone/ca.crt"),
            sae_id=1
        )
        
        # Get status
        print("Getting KME 1 status...")
        status = await kme1_client.get_status()
        print(f"Status: {json.dumps(status, indent=2)}")
        
        # Create OptimizedKMClient for KME 2
        print("\nCreating OptimizedKMClient for KME 2...")
        kme2_client = OptimizedKMClient(
            base_url="https://localhost:14000",
            cert_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), "certs/kme-2-local-zone/client_3.pfx"),
            cert_password="password",
            ca_cert_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), "certs/kme-2-local-zone/ca.crt"),
            sae_id=2
        )
        
        # Get status
        print("Getting KME 2 status...")
        status = await kme2_client.get_status()
        print(f"Status: {json.dumps(status, indent=2)}")
        
        # Test getting encryption key
        print("\nTrying to get encryption key from KME 1...")
        try:
            enc_key = await kme1_client.get_encryption_key(2)
            print(f"Encryption key retrieved: {enc_key['key_ID'] if enc_key and 'key_ID' in enc_key else 'None'}")
        except Exception as e:
            print(f"Failed to get encryption key: {e}")
        
        # Test getting decryption key (only if we got an encryption key)
        if 'enc_key' in locals() and enc_key and 'key_ID' in enc_key:
            print(f"\nTrying to get decryption key from KME 2 with ID {enc_key['key_ID']}...")
            try:
                dec_key = await kme2_client.get_decryption_key(1, enc_key['key_ID'])
                print(f"Decryption key retrieved: {len(dec_key) if dec_key else 0} bytes")
                print(f"Key preview (first 8 bytes): {dec_key[:8].hex() if dec_key and len(dec_key) >= 8 else 'None'}")
            except Exception as e:
                print(f"Failed to get decryption key: {e}")
    
    except Exception as e:
        print(f"Error testing OptimizedKMClient: {e}")

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Test KME server integration")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--legacy", action="store_true", help="Run only the original test function")
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if args.legacy:
        # Run original test for backward compatibility
        await test_kme_status()
    else:
        print("\nQuMail KME Server Integration Test")
        print("=================================\n")
        
        await test_kme_service()
        await test_optimized_km_client()
        
        print("\nTest complete.")

# Run the test
if __name__ == "__main__":
    asyncio.run(main())