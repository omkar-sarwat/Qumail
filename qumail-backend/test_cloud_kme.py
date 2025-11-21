"""
Test Cloud KME Connectivity
Tests connection to Render.com cloud KME servers and quantum key generation
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.services.kme_service import KmeService

async def test_cloud_kme():
    """Test cloud KME server connectivity and key generation"""
    
    print("\n" + "="*80)
    print("CLOUD KME CONNECTIVITY TEST")
    print("="*80)
    
    # Initialize KME service
    print("\n[1/5] Initializing KME Service...")
    kme_service = KmeService()
    print("✓ KME Service initialized")
    
    # Test KME 1 (Sender) connectivity
    print("\n[2/5] Testing KME 1 (Sender) connectivity...")
    print(f"URL: {kme_service.kme_servers[0]['base_url']}")
    
    try:
        status_1 = await kme_service.get_key_status(
            server_id=0,
            slave_sae_id=2  # Test with SAE ID 2 (receiver)
        )
        print(f"✓ KME 1 Status: {status_1}")
    except Exception as e:
        print(f"✗ KME 1 Connection Failed: {e}")
        print(f"  Error Type: {type(e).__name__}")
    
    # Test KME 2 (Receiver) connectivity
    print("\n[3/5] Testing KME 2 (Receiver) connectivity...")
    print(f"URL: {kme_service.kme_servers[1]['base_url']}")
    
    try:
        status_2 = await kme_service.get_key_status(
            server_id=1,
            slave_sae_id=1  # Test with SAE ID 1 (sender)
        )
        print(f"✓ KME 2 Status: {status_2}")
    except Exception as e:
        print(f"✗ KME 2 Connection Failed: {e}")
        print(f"  Error Type: {type(e).__name__}")
    
    # Test key generation from KME 1 (Sender)
    print("\n[4/5] Testing quantum key generation from KME 1 (Sender)...")
    
    try:
        keys = await kme_service.generate_keys(
            kme_id=0,  # KME 1 (Sender)
            count=2    # Request 2 keys
        )
        
        if keys and len(keys) > 0:
            print(f"✓ Generated {len(keys)} quantum keys")
            print(f"  Key 1 ID: {keys[0].get('key_ID', 'N/A')}")
            print(f"  Key 1 Size: {len(keys[0].get('key', ''))} bytes (base64 encoded)")
            if len(keys) > 1:
                print(f"  Key 2 ID: {keys[1].get('key_ID', 'N/A')}")
        else:
            print(f"✗ No keys generated")
            
    except Exception as e:
        print(f"✗ Key Generation Failed: {e}")
        print(f"  Error Type: {type(e).__name__}")
    
    # Test key retrieval from KME 2 (Receiver)
    print("\n[5/5] Testing quantum key retrieval from KME 2 (Receiver)...")
    
    try:
        keys = await kme_service.generate_keys(
            kme_id=1,  # KME 2 (Receiver)
            count=2    # Request 2 keys
        )
        
        if keys and len(keys) > 0:
            print(f"✓ Retrieved {len(keys)} quantum keys")
            print(f"  Key 1 ID: {keys[0].get('key_ID', 'N/A')}")
            print(f"  Key 1 Size: {len(keys[0].get('key', ''))} bytes (base64 encoded)")
            if len(keys) > 1:
                print(f"  Key 2 ID: {keys[1].get('key_ID', 'N/A')}")
        else:
            print(f"✗ No keys retrieved")
            
    except Exception as e:
        print(f"✗ Key Retrieval Failed: {e}")
        print(f"  Error Type: {type(e).__name__}")
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80 + "\n")

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_cloud_kme())
