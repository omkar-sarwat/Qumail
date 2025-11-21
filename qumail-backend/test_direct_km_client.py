"""
Test script to verify direct KM client connection with real KM servers
"""

import os
import sys
import asyncio
import base64
import json
from pathlib import Path

# Make sure Python can find the app module
sys.path.append(str(Path(__file__).parent))

from app.services.direct_km_client import km1_client, km2_client

async def test_km_status():
    """Test KM server status"""
    print("\n=== Testing KM Server Status ===")
    
    try:
        # Check KM1 status
        print("\nChecking KM1 status...")
        km1_status = await km1_client.get_status()
        print(f"KM1 Status: {json.dumps(km1_status, indent=2)}")
        
        # Check KM2 status
        print("\nChecking KM2 status...")
        km2_status = await km2_client.get_status()
        print(f"KM2 Status: {json.dumps(km2_status, indent=2)}")
        
        return True
    except Exception as e:
        print(f"Error checking KM status: {e}")
        return False

async def test_key_status():
    """Test key status"""
    print("\n=== Testing Key Status ===")
    
    try:
        # Check KM1 key status (for SAE 3)
        print("\nChecking KM1 key status for SAE 3...")
        km1_key_status = await km1_client.check_key_status(3)
        print(f"KM1 key status for SAE 3: {json.dumps(km1_key_status, indent=2)}")
        
        # Check KM2 key status (for SAE 1)
        print("\nChecking KM2 key status for SAE 1...")
        km2_key_status = await km2_client.check_key_status(1)
        print(f"KM2 key status for SAE 1: {json.dumps(km2_key_status, indent=2)}")
        
        return True
    except Exception as e:
        print(f"Error checking key status: {e}")
        return False

async def test_key_request():
    """Test requesting encryption keys"""
    print("\n=== Testing Key Request ===")
    
    try:
        # Request encryption key from KM1 (for SAE 3)
        print("\nRequesting encryption key from KM1 for SAE 3...")
        keys = await km1_client.request_enc_keys(3, number=1)
        print(f"Received {len(keys)} keys from KM1")
        
        if keys:
            key_id = keys[0]["key_ID"]
            print(f"Key ID: {key_id}")
            
            # Try to request decryption key from KM2 (for SAE 1)
            print("\nRequesting decryption key from KM2 for SAE 1...")
            dec_keys = await km2_client.request_dec_keys(1, [key_id])
            print(f"Received {len(dec_keys)} decryption keys from KM2")
            
            if dec_keys:
                # Mark key as consumed
                print("\nMarking key as consumed...")
                consumed = await km2_client.mark_key_consumed(key_id)
                print(f"Key marked as consumed: {consumed}")
                
        return True
    except Exception as e:
        print(f"Error requesting keys: {e}")
        return False

async def main():
    """Main test function"""
    print("=== Direct KM Client Test ===")
    
    status_ok = await test_km_status()
    key_status_ok = await test_key_status()
    key_request_ok = await test_key_request()
    
    print("\n=== Test Summary ===")
    print(f"KM Status Test: {'PASS' if status_ok else 'FAIL'}")
    print(f"Key Status Test: {'PASS' if key_status_ok else 'FAIL'}")
    print(f"Key Request Test: {'PASS' if key_request_ok else 'FAIL'}")
    
    # Clean up (close HTTP clients)
    await km1_client.close()
    await km2_client.close()
    
if __name__ == "__main__":
    asyncio.run(main())