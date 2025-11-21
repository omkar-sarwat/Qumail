"""
Comprehensive Quantum Security System Test Suite
Tests one-time-use quantum keys and QuMail-only decryption
"""

import asyncio
import logging
import json
import secrets
from datetime import datetime
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class QuantumSecurityTestSuite:
    """Comprehensive test suite for quantum security features"""
    
    def __init__(self):
        self.test_results = []
        self.quantum_key_manager = None
        self.qumail_encryption = None
        
    async def initialize_quantum_services(self):
        """Initialize quantum services for testing"""
        try:
            logger.info("Initializing quantum services for testing...")
            
            # Import quantum services
            from app.services.km_client_init import get_optimized_km_clients
            from app.services.quantum_key_manager import OneTimeQuantumKeyManager, SecurityLevel
            from app.services.qumail_encryption import QuMailQuantumEncryption
            
            # Get KM clients
            km1_client, km2_client = get_optimized_km_clients()
            
            # Initialize quantum key manager
            self.quantum_key_manager = OneTimeQuantumKeyManager(km1_client, km2_client)
            await self.quantum_key_manager.initialize()
            
            # Initialize QuMail encryption
            self.qumail_encryption = QuMailQuantumEncryption(self.quantum_key_manager)
            
            logger.info("Quantum services initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize quantum services: {e}")
            return False
    
    async def test_one_time_key_generation(self) -> Dict[str, Any]:
        """Test 1: One-time quantum key generation across all security levels"""
        test_name = "One-Time Key Generation"
        logger.info(f"Starting {test_name}...")
        
        try:
            from app.services.quantum_key_manager import SecurityLevel
            
            generated_keys = {}
            
            # Test each security level
            for level in SecurityLevel:
                logger.info(f"Testing {level.name} key generation...")
                
                key_info = await self.quantum_key_manager.get_one_time_key(level)
                
                if not key_info:
                    raise ValueError(f"Failed to generate {level.name} key")
                
                generated_keys[level.name] = {
                    "key_id": key_info["key_id"],
                    "key_size": len(key_info["key_material"]),
                    "expected_size": level.value,
                    "timestamp": key_info["created_at"]
                }
                
                # Verify key size matches security level
                if len(key_info["key_material"]) < level.value:
                    raise ValueError(f"{level.name} key size mismatch: got {len(key_info['key_material'])}, expected {level.value}")
                
                logger.info(f"{level.name} key generated successfully: {key_info['key_id']}")
            
            result = {
                "test_name": test_name,
                "status": "PASSED",
                "generated_keys": generated_keys,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.test_results.append(result)
            logger.info(f"{test_name} PASSED")
            return result
            
        except Exception as e:
            result = {
                "test_name": test_name,
                "status": "FAILED",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.test_results.append(result)
            logger.error(f"{test_name} FAILED: {e}")
            return result
    
    async def test_key_consumption_tracking(self) -> Dict[str, Any]:
        """Test 2: Key consumption tracking prevents reuse"""
        test_name = "Key Consumption Tracking"
        logger.info(f"Starting {test_name}...")
        
        try:
            from app.services.quantum_key_manager import SecurityLevel
            
            # Generate a test key
            key_info = await self.quantum_key_manager.get_one_time_key(SecurityLevel.MEDIUM)
            key_id = key_info["key_id"]
            
            logger.info(f"Generated test key: {key_id}")
            
            # Check initial status (should be unconsumed)
            initial_status = await self.quantum_key_manager.get_key_status(key_id)
            if initial_status.get("consumed", True):
                raise ValueError("New key should not be marked as consumed")
            
            # Mark key as consumed
            await self.quantum_key_manager.mark_key_consumed(
                key_id=key_id,
                user_id="test_user@qumail.com",
                usage_type="TEST_CONSUMPTION"
            )
            
            logger.info(f"Marked key {key_id} as consumed")
            
            # Check status after consumption (should be consumed)
            consumed_status = await self.quantum_key_manager.get_key_status(key_id)
            if not consumed_status.get("consumed", False):
                raise ValueError("Key should be marked as consumed after use")
            
            # Try to use the same key again (should fail)
            try:
                await self.quantum_key_manager.mark_key_consumed(
                    key_id=key_id,
                    user_id="test_user2@qumail.com",
                    usage_type="TEST_REUSE_ATTEMPT"
                )
                raise ValueError("Should not be able to reuse consumed key")
            except ValueError as e:
                if "already consumed" not in str(e):
                    raise ValueError(f"Unexpected error on reuse attempt: {e}")
                logger.info("Key reuse properly prevented")
            
            result = {
                "test_name": test_name,
                "status": "PASSED",
                "key_id": key_id,
                "initial_consumed": initial_status.get("consumed", False),
                "final_consumed": consumed_status.get("consumed", False),
                "reuse_prevented": True,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.test_results.append(result)
            logger.info(f"{test_name} PASSED")
            return result
            
        except Exception as e:
            result = {
                "test_name": test_name,
                "status": "FAILED",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.test_results.append(result)
            logger.error(f"{test_name} FAILED: {e}")
            return result
    
    async def test_qumail_only_encryption(self) -> Dict[str, Any]:
        """Test 3: QuMail-only encryption and obfuscation"""
        test_name = "QuMail-Only Encryption"
        logger.info(f"Starting {test_name}...")
        
        try:
            from app.services.quantum_key_manager import SecurityLevel
            
            test_message = "This is a secret quantum message that should only be readable in QuMail!"
            sender_id = "sender@qumail.com"
            recipient_id = "recipient@qumail.com"
            
            logger.info(f"Testing QuMail-only encryption for message: '{test_message[:50]}...'")
            
            # Encrypt message with QuMail-only protection
            encryption_result = await self.qumail_encryption.encrypt_message(
                message=test_message,
                sender_id=sender_id,
                recipient_id=recipient_id,
                security_level=SecurityLevel.HIGH
            )
            
            # Verify encryption result structure
            required_keys = ["encrypted_data", "key_id", "obfuscated_preview", "app_signature"]
            for key in required_keys:
                if key not in encryption_result:
                    raise ValueError(f"Missing required key in encryption result: {key}")
            
            # Verify obfuscated preview is different from original
            obfuscated = encryption_result["obfuscated_preview"]
            if obfuscated == test_message:
                raise ValueError("Obfuscated preview should differ from original message")
            
            # Verify obfuscated preview looks like random hex
            if not all(c in "0123456789abcdefABCDEF" for c in obfuscated.replace("-", "")):
                logger.warning(f"Obfuscated preview may not look sufficiently random: {obfuscated}")
            
            # Test decryption within QuMail context
            decryption_result = await self.qumail_encryption.decrypt_message(
                encrypted_data=encryption_result["encrypted_data"],
                key_id=encryption_result["key_id"],
                user_id=recipient_id
            )
            
            # Verify decrypted message matches original
            if decryption_result["decrypted_message"] != test_message:
                raise ValueError("Decrypted message does not match original")
            
            # Verify key was consumed
            if not decryption_result.get("key_consumed", False):
                raise ValueError("Key should be marked as consumed after decryption")
            
            result = {
                "test_name": test_name,
                "status": "PASSED",
                "original_message": test_message,
                "obfuscated_preview": obfuscated,
                "encrypted_size": len(encryption_result["encrypted_data"]),
                "key_id": encryption_result["key_id"],
                "key_consumed": decryption_result["key_consumed"],
                "decryption_successful": decryption_result["decrypted_message"] == test_message,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.test_results.append(result)
            logger.info(f"{test_name} PASSED")
            return result
            
        except Exception as e:
            result = {
                "test_name": test_name,
                "status": "FAILED",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.test_results.append(result)
            logger.error(f"{test_name} FAILED: {e}")
            return result
    
    async def test_quantum_otp_encryption(self) -> Dict[str, Any]:
        """Test 4: Quantum One-Time Pad encryption with perfect secrecy"""
        test_name = "Quantum OTP Encryption"
        logger.info(f"Starting {test_name}...")
        
        try:
            # Import the new quantum OTP function
            from app.services.encryption.level1_otp import encrypt_otp_quantum
            
            test_message = "Perfect secrecy test message for quantum OTP encryption!"
            user_email = "test_user@qumail.com"
            
            logger.info(f"Testing quantum OTP encryption for: '{test_message}'")
            
            # Encrypt using quantum OTP
            encryption_result = await encrypt_otp_quantum(
                content=test_message,
                user_email=user_email
            )
            
            # Verify encryption result structure
            required_keys = ["encrypted_content", "algorithm", "metadata", "qumail_data"]
            for key in required_keys:
                if key not in encryption_result:
                    raise ValueError(f"Missing required key in encryption result: {key}")
            
            # Verify algorithm is correct
            if encryption_result["algorithm"] != "Quantum One-Time Pad":
                raise ValueError(f"Expected 'Quantum One-Time Pad', got '{encryption_result['algorithm']}'")
            
            # Verify metadata contains required information
            metadata = encryption_result["metadata"]
            required_metadata = ["key_id", "security_level", "perfect_secrecy", "key_consumed"]
            for key in required_metadata:
                if key not in metadata:
                    raise ValueError(f"Missing required metadata key: {key}")
            
            # Verify perfect secrecy flag
            if not metadata.get("perfect_secrecy", False):
                raise ValueError("Perfect secrecy should be True for OTP encryption")
            
            # Verify key was consumed
            if not metadata.get("key_consumed", False):
                raise ValueError("Key should be marked as consumed")
            
            # Verify encrypted content is different from original
            if encryption_result["encrypted_content"] == test_message:
                raise ValueError("Encrypted content should differ from original")
            
            result = {
                "test_name": test_name,
                "status": "PASSED",
                "original_message": test_message,
                "algorithm": encryption_result["algorithm"],
                "key_id": metadata["key_id"],
                "security_level": metadata["security_level"],
                "perfect_secrecy": metadata["perfect_secrecy"],
                "key_consumed": metadata["key_consumed"],
                "encrypted_size": len(encryption_result["encrypted_content"]),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.test_results.append(result)
            logger.info(f"{test_name} PASSED")
            return result
            
        except Exception as e:
            result = {
                "test_name": test_name,
                "status": "FAILED",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.test_results.append(result)
            logger.error(f"{test_name} FAILED: {e}")
            return result
    
    async def test_security_level_management(self) -> Dict[str, Any]:
        """Test 5: Security level management and key pool status"""
        test_name = "Security Level Management"
        logger.info(f"Starting {test_name}...")
        
        try:
            from app.services.qumail_encryption import QuMailSecurityLevelManager
            from app.services.quantum_key_manager import SecurityLevel
            
            # Initialize security level manager
            security_level_manager = QuMailSecurityLevelManager(self.quantum_key_manager)
            
            # Get key pool status for all levels
            key_pools = await security_level_manager.get_key_pool_status()
            
            logger.info(f"Key pool status: {key_pools}")
            
            # Verify all security levels are represented
            for level in SecurityLevel:
                if level.name not in key_pools:
                    raise ValueError(f"Missing key pool status for {level.name}")
            
            # Get total consumed keys
            total_consumed = await security_level_manager.get_total_consumed_keys()
            
            logger.info(f"Total consumed keys: {total_consumed}")
            
            # Verify consumed keys is a non-negative integer
            if not isinstance(total_consumed, int) or total_consumed < 0:
                raise ValueError(f"Invalid total consumed keys count: {total_consumed}")
            
            # Test level recommendations
            recommendations = {}
            for level in SecurityLevel:
                recommendation = security_level_manager._get_level_recommendation(level)
                recommendations[level.name] = recommendation
                
                if not isinstance(recommendation, str) or len(recommendation) < 10:
                    raise ValueError(f"Invalid recommendation for {level.name}: {recommendation}")
            
            result = {
                "test_name": test_name,
                "status": "PASSED",
                "key_pools": key_pools,
                "total_consumed_keys": total_consumed,
                "level_recommendations": recommendations,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.test_results.append(result)
            logger.info(f"{test_name} PASSED")
            return result
            
        except Exception as e:
            result = {
                "test_name": test_name,
                "status": "FAILED",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.test_results.append(result)
            logger.error(f"{test_name} FAILED: {e}")
            return result
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all quantum security tests and return comprehensive results"""
        logger.info("Starting Comprehensive Quantum Security Test Suite...")
        
        start_time = datetime.utcnow()
        
        # Initialize quantum services first
        initialization_success = await self.initialize_quantum_services()
        
        if not initialization_success:
            return {
                "test_suite": "Quantum Security System",
                "status": "INITIALIZATION_FAILED",
                "total_tests": 0,
                "passed_tests": 0,
                "failed_tests": 0,
                "timestamp": start_time.isoformat(),
                "error": "Failed to initialize quantum services"
            }
        
        # Run all tests
        tests = [
            self.test_one_time_key_generation,
            self.test_key_consumption_tracking,
            self.test_qumail_only_encryption,
            self.test_quantum_otp_encryption,
            self.test_security_level_management
        ]
        
        for test_func in tests:
            try:
                await test_func()
            except Exception as e:
                logger.error(f"Test function {test_func.__name__} failed: {e}")
        
        # Calculate results
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["status"] == "PASSED")
        failed_tests = total_tests - passed_tests
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # Overall test suite result
        overall_status = "PASSED" if failed_tests == 0 else "FAILED"
        
        summary = {
            "test_suite": "Quantum Security System",
            "status": overall_status,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": f"{(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "0%",
            "duration_seconds": duration,
            "timestamp": start_time.isoformat(),
            "completed_at": end_time.isoformat(),
            "detailed_results": self.test_results
        }
        
        logger.info(f"Quantum Security Test Suite completed: {passed_tests}/{total_tests} tests passed")
        
        return summary

# Main test runner function
async def run_quantum_security_tests():
    """Main function to run quantum security tests"""
    test_suite = QuantumSecurityTestSuite()
    results = await test_suite.run_all_tests()
    
    # Print summary
    print("\n" + "="*80)
    print("QUANTUM SECURITY TEST RESULTS")
    print("="*80)
    print(f"Test Suite: {results['test_suite']}")
    print(f"Status: {results['status']}")
    print(f"Tests Passed: {results['passed_tests']}/{results['total_tests']}")
    print(f"Success Rate: {results['success_rate']}")
    print(f"Duration: {results['duration_seconds']:.2f} seconds")
    print("="*80)
    
    # Print individual test results
    if "detailed_results" in results:
        for test_result in results["detailed_results"]:
            status_icon = "✅" if test_result["status"] == "PASSED" else "❌"
            print(f"{status_icon} {test_result['test_name']}: {test_result['status']}")
            
            if test_result["status"] == "FAILED":
                print(f"   Error: {test_result.get('error', 'Unknown error')}")
    
    print("="*80)
    
    return results

if __name__ == "__main__":
    # Run tests if this file is executed directly
    asyncio.run(run_quantum_security_tests())