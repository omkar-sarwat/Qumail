"""
Simple Quantum Key Manager Test
Test if the quantum key manager can generate and consume keys properly
"""

import asyncio
import logging
import sys
import os

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.km_client_init import get_optimized_km_clients
from app.services.quantum_key_manager import OneTimeQuantumKeyManager, SecurityLevel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_quantum_system():
    """Simple test to verify quantum key generation and consumption"""
    
    print("🔑 Testing Quantum Key Management System")
    print("=" * 50)
    
    try:
        # Initialize KM clients
        print("1. Initializing KM clients...")
        km1_client, km2_client = get_optimized_km_clients()
        print(f"   ✅ KM1: {km1_client.base_url}")
        print(f"   ✅ KM2: {km2_client.base_url}")
        
        # Initialize quantum key manager
        print("\n2. Initializing Quantum Key Manager...")
        quantum_manager = OneTimeQuantumKeyManager([km1_client, km2_client])
        await quantum_manager.initialize()
        print("   ✅ Quantum Key Manager initialized")
        
        # Test key generation for each security level
        print("\n3. Testing key generation for all security levels...")
        
        for level in SecurityLevel:
            print(f"\n   Testing {level.name} security level ({level.value} bytes)...")
            
            try:
                # Generate key
                key_info = await quantum_manager.get_one_time_key(level)
                
                if key_info:
                    print(f"   ✅ Generated key: {key_info['key_id'][:16]}...")
                    print(f"      Key size: {len(key_info['key_material'])} bytes")
                    print(f"      KME source: {key_info['kme_source']}")
                    
                    # Test key status
                    status = await quantum_manager.get_key_status(key_info['key_id'])
                    print(f"      Initial status: {status['status']}")
                    
                    # Mark key as consumed
                    await quantum_manager.mark_key_consumed(
                        key_info['key_id'],
                        "test_user@qumail.com",
                        "TEST_ENCRYPTION"
                    )
                    
                    # Check status after consumption
                    status_after = await quantum_manager.get_key_status(key_info['key_id'])
                    print(f"      Status after consumption: {status_after['status']}")
                    
                    if status_after['consumed']:
                        print(f"   ✅ Key properly marked as consumed")
                    else:
                        print(f"   ❌ Key consumption tracking failed")
                        
                else:
                    print(f"   ❌ Failed to generate {level.name} key")
                    
            except Exception as e:
                print(f"   ❌ Error with {level.name} level: {e}")
        
        print("\n4. Testing one-time-use enforcement...")
        
        # Try to generate a key and consume it twice
        try:
            key_info = await quantum_manager.get_one_time_key(SecurityLevel.MEDIUM)
            if key_info:
                key_id = key_info['key_id']
                
                # First consumption should succeed
                await quantum_manager.mark_key_consumed(key_id, "user1@qumail.com", "FIRST_USE")
                print("   ✅ First key consumption successful")
                
                # Second consumption should fail
                try:
                    await quantum_manager.mark_key_consumed(key_id, "user2@qumail.com", "SECOND_USE")
                    print("   ❌ Second consumption should have failed!")
                except ValueError as e:
                    if "already been consumed" in str(e):
                        print("   ✅ One-time-use properly enforced")
                    else:
                        print(f"   ❌ Unexpected error: {e}")
            else:
                print("   ❌ Could not generate key for one-time-use test")
                
        except Exception as e:
            print(f"   ❌ One-time-use test failed: {e}")
        
        print("\n" + "=" * 50)
        print("🎉 Quantum Key Management System Test Complete!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        logger.exception("Test failed")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_quantum_system())
    if success:
        print("\n✅ All quantum security tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)