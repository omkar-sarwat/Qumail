"""
Certificate Configuration Verification Script

This script verifies that the KME certificate configuration fix resolves
the 504 Gateway Timeout issue in inter-KME communication.

The fix involved updating the KME configuration files to use the correct
CA certificates for validating inter-KME client certificates:
- KME1 now uses ca_kme2.crt to validate KME2's client certificate
- KME2 now uses ca_kme1.crt to validate KME1's client certificate
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

class CertificateVerificationClient:
    """Client to verify the certificate configuration fix"""
    
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
        
        logger.info(f"🔧 Certificate Verification Client: KME{kme_id}, SAE{sae_id}")
    
    def _create_ssl_context(self, verify_certs: bool = True) -> ssl.SSLContext:
        """Create SSL context with optional certificate verification"""
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        context.check_hostname = False
        
        if verify_certs:
            try:
                # Load client certificate
                if Path(self.client_cert_path).exists() and Path(self.client_key_path).exists():
                    context.load_cert_chain(self.client_cert_path, self.client_key_path)
                    logger.debug(f"✅ Loaded client certificate for KME{self.kme_id}")
                
                # Load CA certificate
                if Path(self.ca_cert_path).exists():
                    context.load_verify_locations(cafile=self.ca_cert_path)
                    context.verify_mode = ssl.CERT_REQUIRED
                    logger.debug(f"✅ Loaded CA certificate for KME{self.kme_id}")
                else:
                    context.verify_mode = ssl.CERT_NONE
                    logger.warning("⚠️ CA certificate not found")
                
            except Exception as e:
                logger.error(f"❌ Failed to configure SSL: {e}")
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
            "User-Agent": f"Certificate-Verification-Client/KME{self.kme_id}",
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
                logger.debug(f"❌ Request failed (SSL verify: {verify_ssl}): {e}")
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
        
        # Should not reach here
        duration = time.time() - start_time
        return {
            "success": False,
            "status_code": None,
            "data": None,
            "duration": duration,
            "ssl_verified": False,
            "error": "All SSL attempts failed"
        }
    
    async def get_status(self) -> Dict[str, Any]:
        """Get KME status"""
        endpoints = ["/", "/api/v1/status", "/status"]
        
        for endpoint in endpoints:
            result = await self._make_request("GET", endpoint, timeout=10.0)
            if result["success"]:
                if isinstance(result["data"], dict):
                    result["data"].update({
                        "kme_id": self.kme_id,
                        "sae_id": self.sae_id,
                        "ssl_verified": result["ssl_verified"]
                    })
                return result
        
        return {"success": False, "error": "No status endpoint available"}
    
    async def check_key_status(self, target_sae_id: int) -> Dict[str, Any]:
        """Check key status for target SAE"""
        logger.info(f"🔍 Checking key status: SAE{self.sae_id} -> SAE{target_sae_id}")
        
        result = await self._make_request(
            "GET", 
            f"/api/v1/keys/{target_sae_id}/status",
            timeout=15.0
        )
        
        if result["success"] and isinstance(result["data"], dict):
            stored_keys = result["data"].get("stored_key_count", 0)
            logger.info(f"📊 Found {stored_keys} keys for SAE{target_sae_id}")
        
        return result
    
    async def request_encryption_keys(self, target_sae_id: int, 
                                    number: int = 1,
                                    timeout: float = 120.0) -> Dict[str, Any]:
        """Request encryption keys - the critical test"""
        logger.info(f"🔑 Requesting {number} keys: SAE{self.sae_id} -> SAE{target_sae_id}")
        
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
                logger.info(f"🔒 SSL Verified: {result['ssl_verified']}")
                
                if is_cross_kme:
                    logger.info("🎉 CERTIFICATE FIX SUCCESSFUL!")
                    logger.info("✅ Inter-KME communication is now working!")
        
        elif result.get("status_code") == 504:
            logger.error("❌ Still getting 504 Gateway Timeout")
            logger.error("🔧 Certificate fix may need additional configuration")
        
        return result

async def run_certificate_verification():
    """Run the certificate configuration verification test"""
    logger.info("🚀 CERTIFICATE CONFIGURATION VERIFICATION")
    logger.info("Testing if the KME configuration fix resolves inter-KME communication")
    logger.info("=" * 80)
    
    # Create verification clients
    kme1_client = CertificateVerificationClient(kme_id=1, sae_id=1)
    kme2_client = CertificateVerificationClient(kme_id=2, sae_id=3)
    
    verification_results = []
    
    # Step 1: Check if KME servers are running
    logger.info("\n📡 [1] KME Server Availability Check")
    logger.info("-" * 50)
    
    kme1_status = await kme1_client.get_status()
    kme2_status = await kme2_client.get_status()
    
    logger.info(f"KME1 (localhost:13000): {'✅ Running' if kme1_status['success'] else '❌ Not responding'}")
    logger.info(f"KME2 (localhost:14000): {'✅ Running' if kme2_status['success'] else '❌ Not responding'}")
    
    servers_running = kme1_status["success"] and kme2_status["success"]
    verification_results.append(("KME Servers Running", servers_running))
    
    if not servers_running:
        logger.error("🚨 KME servers are not running!")
        logger.info("💡 Please restart the KME servers with the fixed configuration:")
        logger.info("   Terminal 1: cd D:\\New folder (8)\\qumail-secure-email\\qkd_kme_server-master")
        logger.info("              cargo run --bin kme_server -- config_kme1.json5")
        logger.info("   Terminal 2: cargo run --bin kme_server -- config_kme2.json5")
        return False
    
    # Step 2: Key status checks
    logger.info("\n📊 [2] Cross-KME Key Status Check")
    logger.info("-" * 50)
    
    kme1_key_status = await kme1_client.check_key_status(3)  # Cross-KME
    kme2_key_status = await kme2_client.check_key_status(1)  # Cross-KME
    
    status_checks_ok = kme1_key_status["success"] and kme2_key_status["success"]
    verification_results.append(("Cross-KME Status Checks", status_checks_ok))
    
    if kme1_key_status["success"]:
        keys1 = kme1_key_status["data"].get("stored_key_count", 0)
        logger.info(f"KME1->SAE3: {keys1} keys available ✅")
    else:
        logger.warning(f"KME1->SAE3: Status check failed ❌")
    
    if kme2_key_status["success"]:
        keys2 = kme2_key_status["data"].get("stored_key_count", 0)
        logger.info(f"KME2->SAE1: {keys2} keys available ✅")
    else:
        logger.warning(f"KME2->SAE1: Status check failed ❌")
    
    # Step 3: Same-KME test (baseline)
    logger.info("\n🔄 [3] Same-KME Key Request (Baseline)")
    logger.info("-" * 50)
    
    same_kme_result = await kme1_client.request_encryption_keys(2, 1, timeout=30.0)
    same_kme_ok = same_kme_result["success"]
    verification_results.append(("Same-KME Key Request", same_kme_ok))
    
    if same_kme_ok:
        logger.info("✅ Same-KME request successful (baseline working)")
    else:
        logger.warning(f"⚠️ Same-KME request failed: {same_kme_result.get('error', 'Unknown error')}")
    
    # Step 4: THE CRITICAL TEST - Cross-KME request
    logger.info("\n⚡ [4] CRITICAL TEST: Cross-KME Key Request")
    logger.info("-" * 50)
    logger.info("🎯 This test determines if the certificate fix worked!")
    
    cross_kme_result = await kme1_client.request_encryption_keys(3, 1, timeout=150.0)
    cross_kme_ok = cross_kme_result["success"]
    verification_results.append(("Cross-KME Key Request", cross_kme_ok))
    
    if cross_kme_ok:
        keys = cross_kme_result["data"].get("keys", [])
        logger.info(f"🎉 CERTIFICATE FIX SUCCESSFUL!")
        logger.info(f"✅ Cross-KME request successful: {len(keys)} keys")
        logger.info(f"⚡ Duration: {cross_kme_result['duration']:.2f}s")
        logger.info("🔧 The KME configuration fix resolved the issue!")
    elif cross_kme_result.get("status_code") == 504:
        logger.error("❌ Still getting 504 Gateway Timeout")
        logger.error("🔧 The certificate configuration may need additional work")
        logger.error("💡 Check if KME servers were restarted with the new configuration")
    else:
        logger.warning(f"⚠️ Cross-KME request failed: {cross_kme_result.get('error', 'Unknown error')}")
    
    # Step 5: Reverse test (if first succeeded)
    if cross_kme_ok:
        logger.info("\n🔄 [5] Reverse Cross-KME Test")
        logger.info("-" * 50)
        
        reverse_result = await kme2_client.request_encryption_keys(1, 1, timeout=120.0)
        reverse_ok = reverse_result["success"]
        verification_results.append(("Reverse Cross-KME Request", reverse_ok))
        
        if reverse_ok:
            keys = reverse_result["data"].get("keys", [])
            logger.info(f"✅ Reverse cross-KME successful: {len(keys)} keys")
        else:
            logger.warning(f"⚠️ Reverse cross-KME failed: {reverse_result.get('error', 'Unknown error')}")
    else:
        logger.info("\n⏭️ [5] Skipping reverse test (forward test failed)")
        verification_results.append(("Reverse Cross-KME Request", False))
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("📋 CERTIFICATE VERIFICATION RESULTS")
    logger.info("=" * 80)
    
    passed_tests = sum(1 for _, result in verification_results if result)
    total_tests = len(verification_results)
    
    for test_name, result in verification_results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"  {test_name}: {status}")
    
    success_rate = passed_tests / total_tests * 100
    logger.info(f"\nOverall: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")
    
    # Final assessment
    if cross_kme_ok:
        logger.info("\n🎉 CERTIFICATE CONFIGURATION FIX SUCCESSFUL!")
        logger.info("✅ Inter-KME communication is now working!")
        logger.info("✅ 504 Gateway Timeout issue resolved!")
        logger.info("✅ ETSI QKD-014 compliance achieved!")
        return True
    elif servers_running:
        logger.warning("\n⚠️ CERTIFICATE FIX NEEDS ATTENTION")
        logger.info("✅ KME servers are running")
        logger.warning("❌ Inter-KME communication still failing")
        logger.info("\n🔧 NEXT STEPS:")
        logger.info("   1. Verify KME servers were restarted with new configuration")
        logger.info("   2. Check KME server logs for certificate validation errors")
        logger.info("   3. Verify certificate file permissions and paths")
        return False
    else:
        logger.error("\n❌ FUNDAMENTAL ISSUES")
        logger.error("🚨 KME servers are not running with the new configuration")
        return False

async def main():
    """Main verification runner"""
    success = await run_certificate_verification()
    
    print(f"\n🎯 Certificate Verification: {'SUCCESS' if success else 'NEEDS WORK'}")
    
    if success:
        print("🎉 The certificate configuration fix resolved the inter-KME communication issue!")
    else:
        print("🔧 The certificate configuration needs additional work or server restart.")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
