"""
ETSI QKD-014 Cross-KME Communication Test

This script tests the actual ETSI QKD-014 endpoints to verify that the
certificate configuration fix resolved the 504 Gateway Timeout issue
in inter-KME communication.
"""

import asyncio
import httpx
import ssl
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ETSIQKDTester:
    """ETSI QKD-014 endpoint tester"""
    
    def __init__(self, kme_id: int, sae_id: int):
        self.kme_id = kme_id
        self.sae_id = sae_id
        
        # KME configuration
        if kme_id == 1:
            self.kme_url = "https://localhost:13000"
            self.client_cert_path = r"D:\New folder (8)\qumail-secure-email\qkd_kme_server-master\certs\kme-1-local-zone\client_1_cert.pem"
            self.client_key_path = r"D:\New folder (8)\qumail-secure-email\qkd_kme_server-master\certs\kme-1-local-zone\client_1.key"
            self.ca_cert_path = r"D:\New folder (8)\qumail-secure-email\qkd_kme_server-master\certs\kme-1-local-zone\ca.crt"
        else:
            self.kme_url = "https://localhost:14000"
            self.client_cert_path = r"D:\New folder (8)\qumail-secure-email\qkd_kme_server-master\certs\kme-2-local-zone\client_3_cert.pem"
            self.client_key_path = r"D:\New folder (8)\qumail-secure-email\qkd_kme_server-master\certs\kme-2-local-zone\client_3.key"
            self.ca_cert_path = r"D:\New folder (8)\qumail-secure-email\qkd_kme_server-master\certs\kme-2-local-zone\ca.crt"
        
        logger.info(f"🔑 ETSI QKD Tester: KME{kme_id}, SAE{sae_id}")
    
    def _create_ssl_context(self, verify_certs: bool = True) -> ssl.SSLContext:
        """Create SSL context"""
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        context.check_hostname = False
        
        if verify_certs:
            try:
                if Path(self.client_cert_path).exists() and Path(self.client_key_path).exists():
                    context.load_cert_chain(self.client_cert_path, self.client_key_path)
                
                if Path(self.ca_cert_path).exists():
                    context.load_verify_locations(cafile=self.ca_cert_path)
                    context.verify_mode = ssl.CERT_REQUIRED
                else:
                    context.verify_mode = ssl.CERT_NONE
                    
            except Exception as e:
                logger.debug(f"SSL setup failed: {e}")
                context.verify_mode = ssl.CERT_NONE
        else:
            context.verify_mode = ssl.CERT_NONE
        
        return context
    
    async def _make_request(self, method: str, endpoint: str, 
                          data: Optional[Dict] = None,
                          timeout: float = 30.0) -> Dict[str, Any]:
        """Make HTTP request with SSL fallback"""
        start_time = time.time()
        
        url = f"{self.kme_url}{endpoint}"
        headers = {
            "User-Agent": f"ETSI-QKD-014-Tester/KME{self.kme_id}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Try with SSL verification first, then without
        for verify_ssl in [True, False]:
            try:
                ssl_context = self._create_ssl_context(verify_ssl)
                
                async with httpx.AsyncClient(
                    verify=ssl_context, 
                    timeout=timeout
                ) as client:
                    
                    if method.upper() == "GET":
                        response = await client.get(url, headers=headers)
                    elif method.upper() == "POST":
                        response = await client.post(url, json=data, headers=headers)
                    else:
                        raise ValueError(f"Unsupported method: {method}")
                    
                    duration = time.time() - start_time
                    
                    try:
                        result_data = response.json()
                    except:
                        result_data = response.text
                    
                    return {
                        "success": response.status_code < 400,
                        "status_code": response.status_code,
                        "data": result_data,
                        "duration": duration,
                        "ssl_verified": verify_ssl,
                        "error": None
                    }
                        
            except Exception as e:
                if not verify_ssl:  # This was our last attempt
                    duration = time.time() - start_time
                    return {
                        "success": False,
                        "status_code": None,
                        "data": None,
                        "duration": duration,
                        "ssl_verified": False,
                        "error": str(e)
                    }
                continue
        
        duration = time.time() - start_time
        return {
            "success": False,
            "status_code": None,
            "data": None,
            "duration": duration,
            "ssl_verified": False,
            "error": "All SSL attempts failed"
        }
    
    async def test_key_status(self, target_sae_id: int) -> Dict[str, Any]:
        """Test ETSI QKD-014 key status endpoint"""
        logger.info(f"🔍 Testing key status: SAE{self.sae_id} -> SAE{target_sae_id}")
        
        result = await self._make_request(
            "GET", 
            f"/api/v1/keys/{target_sae_id}/status",
            timeout=15.0
        )
        
        if result["success"] and isinstance(result["data"], dict):
            stored_keys = result["data"].get("stored_key_count", 0)
            logger.info(f"📊 Found {stored_keys} keys for SAE{target_sae_id}")
        
        return result
    
    async def test_encryption_keys(self, target_sae_id: int, 
                                 number: int = 1,
                                 timeout: float = 120.0) -> Dict[str, Any]:
        """Test ETSI QKD-014 encryption keys endpoint - THE CRITICAL TEST"""
        logger.info(f"🔑 Testing encryption keys: SAE{self.sae_id} -> SAE{target_sae_id}")
        
        # Determine if this is cross-KME
        target_kme = 1 if target_sae_id in [1, 2] else 2
        is_cross_kme = target_kme != self.kme_id
        
        if is_cross_kme:
            logger.info(f"⚡ Cross-KME request: KME{self.kme_id} -> KME{target_kme}")
            logger.info("🎯 This tests the certificate configuration fix!")
        
        result = await self._make_request(
            "POST",
            f"/api/v1/keys/{target_sae_id}/enc_keys",
            data={"number": number},
            timeout=timeout
        )
        
        if result["success"]:
            if isinstance(result["data"], dict):
                keys = result["data"].get("keys", [])
                logger.info(f"✅ Success! Retrieved {len(keys)} keys in {result['duration']:.2f}s")
                
                if is_cross_kme:
                    logger.info("🎉 CERTIFICATE FIX SUCCESSFUL!")
                    logger.info("✅ Inter-KME communication is working!")
        
        elif result.get("status_code") == 504:
            logger.error("❌ Still getting 504 Gateway Timeout")
            if is_cross_kme:
                logger.error("🔧 Certificate fix did not resolve the issue")
        
        return result

async def run_etsi_qkd_test():
    """Run the ETSI QKD-014 cross-KME communication test"""
    logger.info("🚀 ETSI QKD-014 CROSS-KME COMMUNICATION TEST")
    logger.info("Testing if the certificate fix resolved the 504 Gateway Timeout")
    logger.info("=" * 80)
    
    # Create ETSI QKD testers
    kme1_tester = ETSIQKDTester(kme_id=1, sae_id=1)
    kme2_tester = ETSIQKDTester(kme_id=2, sae_id=3)
    
    test_results = []
    
    # Test 1: Cross-KME key status checks
    logger.info("\n📊 [1] Cross-KME Key Status Check")
    logger.info("-" * 50)
    
    kme1_status = await kme1_tester.test_key_status(3)  # SAE1 -> SAE3 (cross-KME)
    kme2_status = await kme2_tester.test_key_status(1)  # SAE3 -> SAE1 (cross-KME)
    
    status_ok = kme1_status["success"] and kme2_status["success"]
    test_results.append(("Cross-KME Status Checks", status_ok))
    
    if kme1_status["success"]:
        keys1 = kme1_status["data"].get("stored_key_count", 0) if isinstance(kme1_status["data"], dict) else 0
        logger.info(f"KME1->SAE3: {keys1} keys available ✅")
    else:
        logger.warning(f"KME1->SAE3: Failed - {kme1_status.get('error', 'Unknown error')}")
    
    if kme2_status["success"]:
        keys2 = kme2_status["data"].get("stored_key_count", 0) if isinstance(kme2_status["data"], dict) else 0
        logger.info(f"KME2->SAE1: {keys2} keys available ✅")
    else:
        logger.warning(f"KME2->SAE1: Failed - {kme2_status.get('error', 'Unknown error')}")
    
    # Test 2: Same-KME encryption keys (baseline)
    logger.info("\n🔄 [2] Same-KME Encryption Keys (Baseline)")
    logger.info("-" * 50)
    
    same_kme_result = await kme1_tester.test_encryption_keys(2, 1, timeout=30.0)  # SAE1 -> SAE2
    same_kme_ok = same_kme_result["success"]
    test_results.append(("Same-KME Encryption Keys", same_kme_ok))
    
    if same_kme_ok:
        logger.info("✅ Same-KME encryption keys working (baseline confirmed)")
    else:
        error_msg = same_kme_result.get("error", f"HTTP {same_kme_result.get('status_code', 'unknown')}")
        logger.warning(f"⚠️ Same-KME encryption keys failed: {error_msg}")
    
    # Test 3: THE CRITICAL TEST - Cross-KME encryption keys
    logger.info("\n⚡ [3] CRITICAL TEST: Cross-KME Encryption Keys")
    logger.info("-" * 50)
    logger.info("🎯 This test determines if the certificate fix resolved the 504 Gateway Timeout!")
    
    cross_kme_result = await kme1_tester.test_encryption_keys(3, 1, timeout=150.0)  # SAE1 -> SAE3
    cross_kme_ok = cross_kme_result["success"]
    test_results.append(("Cross-KME Encryption Keys", cross_kme_ok))
    
    if cross_kme_ok:
        keys = cross_kme_result["data"].get("keys", []) if isinstance(cross_kme_result["data"], dict) else []
        logger.info(f"🎉 CERTIFICATE FIX SUCCESSFUL!")
        logger.info(f"✅ Cross-KME encryption keys working: {len(keys)} keys")
        logger.info(f"⚡ Duration: {cross_kme_result['duration']:.2f}s")
        logger.info("🔧 The certificate configuration fix resolved the issue!")
    elif cross_kme_result.get("status_code") == 504:
        logger.error("❌ Still getting 504 Gateway Timeout")
        logger.error("🔧 Certificate fix did not resolve the inter-KME communication issue")
        logger.error("💡 Additional investigation needed")
    else:
        error_msg = cross_kme_result.get("error", f"HTTP {cross_kme_result.get('status_code', 'unknown')}")
        logger.warning(f"⚠️ Cross-KME encryption keys failed: {error_msg}")
    
    # Test 4: Reverse cross-KME test (if first succeeded)
    if cross_kme_ok:
        logger.info("\n🔄 [4] Reverse Cross-KME Test")
        logger.info("-" * 50)
        
        reverse_result = await kme2_tester.test_encryption_keys(1, 1, timeout=120.0)  # SAE3 -> SAE1
        reverse_ok = reverse_result["success"]
        test_results.append(("Reverse Cross-KME Keys", reverse_ok))
        
        if reverse_ok:
            keys = reverse_result["data"].get("keys", []) if isinstance(reverse_result["data"], dict) else []
            logger.info(f"✅ Reverse cross-KME successful: {len(keys)} keys")
        else:
            error_msg = reverse_result.get("error", f"HTTP {reverse_result.get('status_code', 'unknown')}")
            logger.warning(f"⚠️ Reverse cross-KME failed: {error_msg}")
    else:
        logger.info("\n⏭️ [4] Skipping reverse test (forward test failed)")
        test_results.append(("Reverse Cross-KME Keys", False))
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("📋 ETSI QKD-014 TEST RESULTS")
    logger.info("=" * 80)
    
    passed_tests = sum(1 for _, result in test_results if result)
    total_tests = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"  {test_name}: {status}")
    
    success_rate = passed_tests / total_tests * 100
    logger.info(f"\nOverall: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")
    
    # Final assessment
    if cross_kme_ok:
        logger.info("\n🎉 BREAKTHROUGH: CERTIFICATE FIX SUCCESSFUL!")
        logger.info("✅ Inter-KME communication is now working!")
        logger.info("✅ 504 Gateway Timeout issue RESOLVED!")
        logger.info("✅ ETSI QKD-014 cross-KME compliance ACHIEVED!")
        return True
    elif same_kme_ok:
        logger.warning("\n⚠️ PARTIAL SUCCESS")
        logger.info("✅ Same-KME communication works")
        logger.warning("❌ Cross-KME communication still failing")
        logger.info("\n🔧 NEXT STEPS:")
        logger.info("   1. Check KME server logs for certificate errors")
        logger.info("   2. Verify inter-KME certificate configuration")
        logger.info("   3. Test inter-KME SSL handshake directly")
        return False
    else:
        logger.error("\n❌ FUNDAMENTAL ISSUES")
        logger.error("🚨 Basic QKD functionality is not working")
        logger.info("💡 Check KME server configuration and certificates")
        return False

async def main():
    """Main test runner"""
    success = await run_etsi_qkd_test()
    
    print(f"\n🎯 ETSI QKD-014 Test: {'SUCCESS' if success else 'NEEDS WORK'}")
    
    if success:
        print("🎉 The certificate configuration fix resolved the inter-KME communication issue!")
        print("✅ Cross-KME quantum key distribution is now working!")
    else:
        print("🔧 Additional work needed on the certificate configuration.")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
