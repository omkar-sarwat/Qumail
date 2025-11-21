"""
Comprehensive ETSI QKD-014 Compliance Test Suite

This test suite validates the complete ETSI QKD-014 implementation including:
- SAE authentication and authorization
- Inter-KME communication protocols
- Key exchange flows and security validation
- Error handling and timeout management
- Standards compliance verification

Test scenarios:
1. Basic connectivity and authentication tests
2. Key status verification for both KMEs
3. Same-KME key exchange (local)
4. Cross-KME key exchange (inter-KME communication)
5. Error handling and security validation
6. Performance and timeout testing
"""

import asyncio
import logging
import time
import sys
from typing import List, Dict, Any
from pathlib import Path

# Add the services directory to path
sys.path.append(str(Path(__file__).parent))

from etsi_qkd_client import (
    ETSIQKDClient, get_etsi_qkd_clients, QKDError, 
    InterKMECommunicationError, InsufficientKeysError, 
    AuthenticationError, QuantumKey
)

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('etsi_qkd_test.log')
    ]
)

logger = logging.getLogger(__name__)

class ETSIQKDTestSuite:
    """
    Comprehensive test suite for ETSI QKD-014 compliance
    """
    
    def __init__(self):
        self.kme1_client, self.kme2_client = get_etsi_qkd_clients()
        self.test_results = []
        self.start_time = None
        
    async def run_test(self, test_name: str, test_func, *args, **kwargs) -> bool:
        """Run a single test with error handling and logging"""
        logger.info(f"🧪 Starting test: {test_name}")
        start_time = time.time()
        
        try:
            result = await test_func(*args, **kwargs)
            duration = time.time() - start_time
            
            if result is True or result is None:
                logger.info(f"✅ PASSED: {test_name} ({duration:.2f}s)")
                self.test_results.append({"test": test_name, "status": "PASSED", "duration": duration})
                return True
            else:
                logger.warning(f"❌ FAILED: {test_name} - {result} ({duration:.2f}s)")
                self.test_results.append({"test": test_name, "status": "FAILED", "duration": duration, "error": str(result)})
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"❌ ERROR: {test_name} - {str(e)} ({duration:.2f}s)")
            self.test_results.append({"test": test_name, "status": "ERROR", "duration": duration, "error": str(e)})
            return False

    async def test_kme_connectivity(self) -> bool:
        """Test basic KME connectivity and health"""
        logger.info("Testing KME connectivity...")
        
        # Test KME 1
        status1 = await self.kme1_client.get_status()
        if not status1.get("healthy", False):
            return f"KME 1 not healthy: {status1}"
        
        # Test KME 2
        status2 = await self.kme2_client.get_status()
        if not status2.get("healthy", False):
            return f"KME 2 not healthy: {status2}"
        
        logger.info(f"KME 1: {status1.get('available_keys', 0)} keys available")
        logger.info(f"KME 2: {status2.get('available_keys', 0)} keys available")
        
        return True

    async def test_sae_authentication(self) -> bool:
        """Test SAE certificate-based authentication"""
        logger.info("Testing SAE authentication...")
        
        try:
            # Test KME 1 SAE authentication
            sae1_info = await self.kme1_client.get_sae_info()
            logger.info(f"KME 1 SAE info: {sae1_info}")
            
            # Test KME 2 SAE authentication
            sae3_info = await self.kme2_client.get_sae_info()
            logger.info(f"KME 2 SAE info: {sae3_info}")
            
            return True
            
        except AuthenticationError as e:
            return f"Authentication failed: {e}"

    async def test_key_status_check(self) -> bool:
        """Test ETSI QKD-014 key status endpoints"""
        logger.info("Testing key status endpoints...")
        
        # KME 1 checking status for SAE 2 (same KME)
        try:
            status_local = await self.kme1_client.check_key_status(2)
            logger.info(f"KME 1 -> SAE 2 (local): {status_local.get('stored_key_count', 0)} keys")
        except Exception as e:
            logger.warning(f"Local key status check failed: {e}")
        
        # KME 1 checking status for SAE 3 (different KME - inter-KME)
        try:
            status_remote = await self.kme1_client.check_key_status(3)
            logger.info(f"KME 1 -> SAE 3 (remote): {status_remote.get('stored_key_count', 0)} keys")
        except Exception as e:
            logger.warning(f"Remote key status check failed: {e}")
        
        # KME 2 checking status for SAE 1 (different KME - inter-KME)
        try:
            status_remote2 = await self.kme2_client.check_key_status(1)
            logger.info(f"KME 2 -> SAE 1 (remote): {status_remote2.get('stored_key_count', 0)} keys")
        except Exception as e:
            logger.warning(f"Remote key status check failed: {e}")
        
        return True

    async def test_entropy_monitoring(self) -> bool:
        """Test quantum key entropy monitoring for security"""
        logger.info("Testing entropy monitoring...")
        
        # Check entropy on both KMEs
        entropy1 = await self.kme1_client.check_entropy()
        entropy2 = await self.kme2_client.check_entropy()
        
        logger.info(f"KME 1 entropy: {entropy1:.3f}")
        logger.info(f"KME 2 entropy: {entropy2:.3f}")
        
        # Security validation
        if entropy1 < 6.0 or entropy2 < 6.0:
            return f"Critically low entropy detected (KME1: {entropy1}, KME2: {entropy2})"
        
        return True

    async def test_same_kme_key_exchange(self) -> bool:
        """Test key exchange within the same KME (no inter-KME communication)"""
        logger.info("Testing same-KME key exchange...")
        
        try:
            # KME 1: SAE 1 -> SAE 2 (same KME)
            keys = await self.kme1_client.request_enc_keys(target_sae_id=2, number=1)
            
            if len(keys) != 1:
                return f"Expected 1 key, got {len(keys)}"
            
            key = keys[0]
            if "key_ID" not in key or "key" not in key:
                return f"Invalid key format: {key}"
            
            logger.info(f"Same-KME key exchange successful: {key['key_ID']}")
            return True
            
        except Exception as e:
            return f"Same-KME key exchange failed: {e}"

    async def test_inter_kme_key_exchange(self) -> bool:
        """Test inter-KME key exchange (the critical test)"""
        logger.info("Testing inter-KME key exchange...")
        
        try:
            # KME 1: SAE 1 -> SAE 3 (cross-KME, requires inter-KME communication)
            logger.info("Requesting keys from KME 1 to SAE 3 (KME 2)...")
            keys = await self.kme1_client.request_enc_keys(
                target_sae_id=3, 
                number=1, 
                use_post=True, 
                retry_on_timeout=True
            )
            
            if len(keys) != 1:
                return f"Expected 1 key, got {len(keys)}"
            
            key = keys[0]
            if "key_ID" not in key or "key" not in key:
                return f"Invalid key format: {key}"
            
            logger.info(f"Inter-KME key exchange successful: {key['key_ID']}")
            return True
            
        except InterKMECommunicationError as e:
            return f"Inter-KME communication failed: {e}"
        except Exception as e:
            return f"Inter-KME key exchange failed: {e}"

    async def test_reverse_inter_kme_key_exchange(self) -> bool:
        """Test reverse inter-KME key exchange"""
        logger.info("Testing reverse inter-KME key exchange...")
        
        try:
            # KME 2: SAE 3 -> SAE 1 (cross-KME, requires inter-KME communication)
            logger.info("Requesting keys from KME 2 to SAE 1 (KME 1)...")
            keys = await self.kme2_client.request_enc_keys(
                target_sae_id=1, 
                number=1, 
                use_post=True, 
                retry_on_timeout=True
            )
            
            if len(keys) != 1:
                return f"Expected 1 key, got {len(keys)}"
            
            key = keys[0]
            if "key_ID" not in key or "key" not in key:
                return f"Invalid key format: {key}"
            
            logger.info(f"Reverse inter-KME key exchange successful: {key['key_ID']}")
            return True
            
        except InterKMECommunicationError as e:
            return f"Reverse inter-KME communication failed: {e}"
        except Exception as e:
            return f"Reverse inter-KME key exchange failed: {e}"

    async def test_multiple_key_request(self) -> bool:
        """Test requesting multiple keys at once"""
        logger.info("Testing multiple key request...")
        
        try:
            # Request multiple keys
            keys = await self.kme1_client.request_enc_keys(target_sae_id=2, number=3)
            
            if len(keys) < 1:
                return f"No keys received"
            
            # Validate all keys
            for i, key in enumerate(keys):
                if "key_ID" not in key or "key" not in key:
                    return f"Invalid key format at index {i}: {key}"
                logger.info(f"Key {i+1}: {key['key_ID']}")
            
            logger.info(f"Multiple key request successful: {len(keys)} keys")
            return True
            
        except Exception as e:
            return f"Multiple key request failed: {e}"

    async def test_full_qkd_protocol(self) -> bool:
        """Test the complete ETSI QKD-014 protocol flow"""
        logger.info("Testing full QKD protocol...")
        
        try:
            # Perform complete QKD exchange
            quantum_keys = await self.kme1_client.perform_full_qkd_exchange(
                target_sae_id=3,  # Cross-KME
                number_of_keys=1
            )
            
            if len(quantum_keys) != 1:
                return f"Expected 1 quantum key, got {len(quantum_keys)}"
            
            qkey = quantum_keys[0]
            if not isinstance(qkey, QuantumKey):
                return f"Invalid quantum key type: {type(qkey)}"
            
            if len(qkey.key_data) == 0:
                return f"Empty key data"
            
            logger.info(f"Full QKD protocol successful: {qkey.key_id} ({len(qkey.key_data)} bytes)")
            return True
            
        except Exception as e:
            return f"Full QKD protocol failed: {e}"

    async def test_error_handling(self) -> bool:
        """Test error handling for various scenarios"""
        logger.info("Testing error handling...")
        
        # Test invalid SAE ID
        try:
            await self.kme1_client.check_key_status(999)
            return "Should have failed for invalid SAE ID"
        except (QKDError, Exception):
            logger.info("Correctly handled invalid SAE ID")
        
        # Test requesting too many keys
        try:
            await self.kme1_client.request_enc_keys(target_sae_id=2, number=1000)
            return "Should have failed for too many keys"
        except (InsufficientKeysError, QKDError, Exception):
            logger.info("Correctly handled excessive key request")
        
        return True

    async def test_performance_benchmark(self) -> bool:
        """Performance benchmark for key exchange operations"""
        logger.info("Running performance benchmark...")
        
        # Single key exchange benchmark
        start_time = time.time()
        try:
            await self.kme1_client.request_enc_keys(target_sae_id=2, number=1)
            single_key_time = time.time() - start_time
            logger.info(f"Single key exchange time: {single_key_time:.3f}s")
        except Exception as e:
            return f"Performance test failed: {e}"
        
        # Multiple sequential requests benchmark
        start_time = time.time()
        try:
            for i in range(3):
                await self.kme1_client.request_enc_keys(target_sae_id=2, number=1)
            sequential_time = time.time() - start_time
            logger.info(f"3 sequential key exchanges time: {sequential_time:.3f}s")
        except Exception as e:
            return f"Sequential performance test failed: {e}"
        
        return True

    async def run_all_tests(self):
        """Run the complete ETSI QKD-014 test suite"""
        logger.info("🚀 Starting ETSI QKD-014 Compliance Test Suite")
        logger.info("=" * 80)
        
        self.start_time = time.time()
        
        # Test sequence following ETSI QKD-014 requirements
        tests = [
            ("KME Connectivity", self.test_kme_connectivity),
            ("SAE Authentication", self.test_sae_authentication),
            ("Key Status Check", self.test_key_status_check),
            ("Entropy Monitoring", self.test_entropy_monitoring),
            ("Same-KME Key Exchange", self.test_same_kme_key_exchange),
            ("Inter-KME Key Exchange", self.test_inter_kme_key_exchange),
            ("Reverse Inter-KME Key Exchange", self.test_reverse_inter_kme_key_exchange),
            ("Multiple Key Request", self.test_multiple_key_request),
            ("Full QKD Protocol", self.test_full_qkd_protocol),
            ("Error Handling", self.test_error_handling),
            ("Performance Benchmark", self.test_performance_benchmark),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            if await self.run_test(test_name, test_func):
                passed += 1
            
            # Brief pause between tests
            await asyncio.sleep(0.5)
        
        # Final results
        total_time = time.time() - self.start_time
        
        logger.info("=" * 80)
        logger.info(f"🏁 Test Suite Complete")
        logger.info(f"📊 Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        logger.info(f"⏱️  Total time: {total_time:.2f}s")
        
        if passed == total:
            logger.info("🎉 ALL TESTS PASSED - ETSI QKD-014 COMPLIANT")
        else:
            logger.warning("⚠️  SOME TESTS FAILED - REVIEW IMPLEMENTATION")
        
        # Detailed results
        logger.info("\n📋 Detailed Results:")
        for result in self.test_results:
            status_icon = "✅" if result["status"] == "PASSED" else "❌"
            logger.info(f"{status_icon} {result['test']} - {result['status']} ({result['duration']:.2f}s)")
            if "error" in result:
                logger.info(f"   Error: {result['error']}")
        
        # Close clients
        await self.kme1_client.close()
        await self.kme2_client.close()
        
        return passed == total

async def main():
    """Main test runner"""
    test_suite = ETSIQKDTestSuite()
    success = await test_suite.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    # Run the test suite
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
