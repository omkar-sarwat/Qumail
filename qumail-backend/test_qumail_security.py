#!/usr/bin/env python3
"""
Comprehensive test suite for QuMail Quantum Security System
Tests all security levels with one-time keys and QuMail-exclusive decryption
"""

import asyncio
import json
import sys
import os
from datetime import datetime, timezone
import traceback

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.services.quantum_key_manager import OneTimeQuantumKeyManager, SecurityLevel
from app.services.qumail_encryption import QuMailQuantumEncryption
from app.security.qumail_quantum_cipher import encrypt_for_qumail_only, decrypt_for_qumail_only

class QuMailSecurityValidator:
    """Comprehensive validation of QuMail quantum security system"""
    
    def __init__(self):
        self.key_manager = None
        self.encryption_service = None
        self.test_results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_status": "UNKNOWN",
            "security_levels_tested": [],
            "one_time_key_tests": {},
            "encryption_format_tests": {},
            "qumail_exclusivity_tests": {},
            "performance_tests": {},
            "security_violations": [],
            "recommendations": []
        }
    
    async def initialize_system(self):
        """Initialize the quantum security system"""
        try:
            print("🔒 Initializing REAL QuMail Quantum Security System...")
            print("🌟 Connecting to REAL KME servers at localhost:8010 and localhost:8020")
            
            # Import real KM clients from production system
            from app.services.optimized_km_client import OptimizedKMClient
            
            # Create REAL KM clients connecting to actual KME servers
            real_km_clients = [
                OptimizedKMClient(
                    base_url="https://127.0.0.1:8010",
                    sae_id="25840139-0dd4-49ae-ba1e-b86731601803",
                    ca_cert_path="../next-door-key-simulator/certs/ca.crt.pem",
                    client_cert_path="../next-door-key-simulator/certs/sae-1.crt.pem",
                    client_key_path="../next-door-key-simulator/certs/sae-1.key.pem"
                ),
                OptimizedKMClient(
                    base_url="https://127.0.0.1:8020", 
                    sae_id="c565d5aa-8670-4446-8471-b0e53e315d2a",
                    ca_cert_path="../next-door-key-simulator/certs/ca.crt.pem",
                    client_cert_path="../next-door-key-simulator/certs/sae-2.crt.pem",
                    client_key_path="../next-door-key-simulator/certs/sae-2.key.pem"
                )
            ]
            
            print("✅ Real KME clients created successfully")
            
            # Initialize key manager with REAL KM clients
            self.key_manager = OneTimeQuantumKeyManager(real_km_clients)
            
            # Initialize encryption service
            self.encryption_service = QuMailQuantumEncryption(self.key_manager)
            
            print("✅ System initialization complete")
            return True
            
        except Exception as e:
            print(f"❌ System initialization failed: {e}")
            self.test_results["initialization_error"] = str(e)
            return False
    
    async def run_comprehensive_validation(self):
        """Run complete validation suite"""
        print("\n" + "="*60)
        print("🚀 STARTING COMPREHENSIVE QUMAIL SECURITY VALIDATION")
        print("="*60)
        
        if not await self.initialize_system():
            return self.test_results
        
        # Test 1: Security Level Integration
        await self.test_all_security_levels()
        
        # Test 2: One-Time Key Enforcement
        await self.test_one_time_key_enforcement()
        
        # Test 3: QuMail Exclusivity
        await self.test_qumail_exclusivity()
        
        # Test 4: Performance Validation
        await self.test_performance_requirements()
        
        # Test 5: System Security Validation
        await self.run_system_security_validation()
        
        # Generate final report
        self.generate_final_report()
        
        return self.test_results
    
    async def test_all_security_levels(self):
        """Test quantum key generation for all security levels"""
        print("\n📊 Testing All Security Levels...")
        
        test_messages = {
            SecurityLevel.LOW: "Low security test message",
            SecurityLevel.MEDIUM: "Medium security confidential data",
            SecurityLevel.HIGH: "High security classified information",
            SecurityLevel.ULTRA: "Ultra security top secret data",
            SecurityLevel.CLASSIFIED: "Classified maximum security intelligence"
        }
        
        for security_level in SecurityLevel:
            level_name = security_level.name
            print(f"\n  🔐 Testing {level_name} level...")
            
            try:
                # Get quantum key for this level
                quantum_key = await self.key_manager.get_one_time_quantum_key_for_level(
                    security_level, f"test_user_{level_name}", "SECURITY_TEST"
                )
                
                if quantum_key:
                    print(f"    ✅ Quantum key generated - ID: {quantum_key['key_id']}")
                    print(f"    📏 Key size: {len(quantum_key['key_material'])} bytes")
                    print(f"    🎲 Entropy score: {quantum_key.get('quality_score', 'N/A')}")
                    
                    # Test encryption with this key
                    test_message = test_messages[security_level]
                    encrypted_data = await self.encryption_service.encrypt_message(
                        test_message, f"test_user_{level_name}", security_level
                    )
                    
                    if encrypted_data:
                        print(f"    🔒 Message encrypted successfully")
                        print(f"    📊 Encrypted format: {encrypted_data['encrypted_message'][:50]}...")
                        
                        # Mark key as consumed to test one-time usage
                        consumption_success = await self.key_manager.mark_key_consumed_forever(
                            quantum_key['key_id'], f"test_user_{level_name}", test_message, "SECURITY_TEST"
                        )
                        
                        if consumption_success:
                            print(f"    ✅ Key properly consumed and marked as used")
                        else:
                            print(f"    ❌ Key consumption failed")
                        
                        self.test_results["security_levels_tested"].append(level_name)
                        self.test_results["one_time_key_tests"][level_name] = {
                            "key_generated": True,
                            "encryption_successful": True,
                            "key_consumed": consumption_success,
                            "key_size_bytes": len(quantum_key['key_material']),
                            "entropy_score": quantum_key.get('quality_score', 0.0)
                        }
                    else:
                        print(f"    ❌ Encryption failed")
                        self.test_results["one_time_key_tests"][level_name] = {
                            "key_generated": True,
                            "encryption_successful": False
                        }
                else:
                    print(f"    ❌ Key generation failed")
                    self.test_results["one_time_key_tests"][level_name] = {
                        "key_generated": False
                    }
                    
            except Exception as e:
                print(f"    ❌ Error testing {level_name}: {e}")
                self.test_results["one_time_key_tests"][level_name] = {
                    "error": str(e)
                }
    
    async def test_one_time_key_enforcement(self):
        """Test that keys cannot be reused"""
        print("\n🔒 Testing One-Time Key Enforcement...")
        
        try:
            # Generate a test key
            test_key = await self.key_manager.get_one_time_quantum_key_for_level(
                SecurityLevel.MEDIUM, "one_time_test_user", "REUSE_TEST"
            )
            
            if test_key:
                key_id = test_key['key_id']
                print(f"  📋 Generated test key: {key_id}")
                
                # First consumption (should succeed)
                first_use = await self.key_manager.mark_key_consumed_forever(
                    key_id, "one_time_test_user", "first message", "REUSE_TEST"
                )
                
                print(f"  ✅ First use result: {first_use}")
                
                # Second consumption attempt (should fail)
                try:
                    second_use = await self.key_manager.mark_key_consumed_forever(
                        key_id, "one_time_test_user", "second message", "REUSE_TEST"
                    )
                    
                    if second_use:
                        print(f"  ❌ SECURITY VIOLATION: Key reuse was allowed!")
                        self.test_results["security_violations"].append({
                            "type": "KEY_REUSE_ALLOWED",
                            "severity": "CRITICAL",
                            "key_id": key_id
                        })
                    else:
                        print(f"  ✅ Key reuse properly prevented")
                        
                except ValueError as e:
                    if "already consumed" in str(e):
                        print(f"  ✅ Key reuse properly rejected with exception: {e}")
                    else:
                        print(f"  ❓ Unexpected error: {e}")
                
                self.test_results["encryption_format_tests"]["one_time_enforcement"] = {
                    "first_use_success": first_use,
                    "reuse_prevented": not second_use if 'second_use' in locals() else True
                }
            else:
                print(f"  ❌ Failed to generate test key")
                
        except Exception as e:
            print(f"  ❌ One-time key test failed: {e}")
    
    async def test_qumail_exclusivity(self):
        """Test QuMail-exclusive encryption format"""
        print("\n🔐 Testing QuMail Exclusivity...")
        
        try:
            test_message = "This should only decrypt in QuMail application"
            test_key = os.urandom(32)  # 256-bit key
            
            # Test QuMail-exclusive encryption
            encrypted_gibberish = encrypt_for_qumail_only(
                message=test_message,
                quantum_key=test_key,
                key_id="qumail_exclusivity_test",
                security_level="HIGH"
            )
            
            print(f"  📄 Original message: {test_message}")
            print(f"  🔒 Encrypted format: {encrypted_gibberish[:80]}...")
            
            # Validate gibberish characteristics
            looks_like_gibberish = self._validate_gibberish_format(encrypted_gibberish)
            contains_readable_text = self._contains_readable_text(encrypted_gibberish)
            
            print(f"  🎭 Looks like gibberish: {looks_like_gibberish}")
            print(f"  📖 Contains readable text: {contains_readable_text}")
            
            # Test QuMail-exclusive decryption
            try:
                decrypted_message = decrypt_for_qumail_only(
                    encrypted_data=encrypted_gibberish,
                    quantum_key=test_key,
                    expected_key_id="qumail_exclusivity_test"
                )
                
                decryption_success = (decrypted_message == test_message)
                print(f"  🔓 QuMail decryption successful: {decryption_success}")
                
                if decryption_success:
                    print(f"  ✅ Decrypted message: {decrypted_message}")
                
            except Exception as e:
                print(f"  ❌ QuMail decryption failed: {e}")
                decryption_success = False
            
            self.test_results["qumail_exclusivity_tests"] = {
                "looks_like_gibberish": looks_like_gibberish,
                "contains_readable_text": contains_readable_text,
                "qumail_decryption_works": decryption_success,
                "encrypted_length": len(encrypted_gibberish),
                "sample_output": encrypted_gibberish[:100]
            }
            
        except Exception as e:
            print(f"  ❌ QuMail exclusivity test failed: {e}")
            self.test_results["qumail_exclusivity_tests"] = {"error": str(e)}
    
    async def test_performance_requirements(self):
        """Test system performance"""
        print("\n⚡ Testing Performance Requirements...")
        
        import time
        
        performance_results = {}
        
        # Test key generation speed for each level
        for security_level in SecurityLevel:
            level_name = security_level.name
            
            start_time = time.time()
            test_key = await self.key_manager.get_one_time_quantum_key_for_level(
                security_level, f"perf_user_{level_name}", "PERFORMANCE_TEST"
            )
            generation_time = (time.time() - start_time) * 1000  # Convert to ms
            
            print(f"  📊 {level_name} key generation: {generation_time:.2f}ms")
            
            performance_results[level_name] = {
                "generation_time_ms": generation_time,
                "acceptable": generation_time < 5000  # 5 second threshold
            }
            
            # Clean up test key
            if test_key:
                await self.key_manager.mark_key_consumed_forever(
                    test_key["key_id"], f"perf_user_{level_name}", "cleanup", "PERFORMANCE_TEST"
                )
        
        self.test_results["performance_tests"] = performance_results
    
    async def run_system_security_validation(self):
        """Run the comprehensive security validation from key manager"""
        print("\n🛡️ Running System Security Validation...")
        
        try:
            validation_results = await self.key_manager.comprehensive_security_validation()
            
            print(f"  📋 Validation ID: {validation_results['validation_id']}")
            print(f"  🎯 Overall Status: {validation_results['overall_status']}")
            print(f"  📊 Security Score: {validation_results.get('security_score', 'N/A')}")
            
            if validation_results.get('security_violations'):
                print(f"  ⚠️ Security Violations Found: {len(validation_results['security_violations'])}")
                for violation in validation_results['security_violations']:
                    print(f"    - {violation['violation']} ({violation['severity']})")
            else:
                print(f"  ✅ No security violations detected")
            
            self.test_results["system_validation"] = validation_results
            
        except Exception as e:
            print(f"  ❌ System validation failed: {e}")
            self.test_results["system_validation"] = {"error": str(e)}
    
    def _validate_gibberish_format(self, text: str) -> bool:
        """Check if text appears as gibberish"""
        # Should not contain common English words
        common_words = ['the', 'and', 'or', 'message', 'email', 'hello', 'test']
        has_common_words = any(word in text.lower() for word in common_words)
        
        # Should have good mix of characters
        has_mixed_chars = (
            any(c.isupper() for c in text) and
            any(c.islower() for c in text) and
            any(c.isdigit() for c in text)
        )
        
        return not has_common_words and has_mixed_chars and len(text) > 30
    
    def _contains_readable_text(self, text: str) -> bool:
        """Check if text contains readable content"""
        readable_words = ['message', 'email', 'hello', 'test', 'the', 'and']
        return any(word in text.lower() for word in readable_words)
    
    def generate_final_report(self):
        """Generate final validation report"""
        print("\n" + "="*60)
        print("📊 FINAL VALIDATION REPORT")
        print("="*60)
        
        # Count successful tests
        successful_levels = len([
            level for level, results in self.test_results["one_time_key_tests"].items()
            if results.get("encryption_successful", False)
        ])
        
        total_levels = len(SecurityLevel)
        security_violations = len(self.test_results["security_violations"])
        
        # Determine overall status
        if successful_levels == total_levels and security_violations == 0:
            self.test_results["overall_status"] = "PASS"
            status_emoji = "✅"
        elif successful_levels > 0 and security_violations == 0:
            self.test_results["overall_status"] = "PASS_WITH_WARNINGS"
            status_emoji = "⚠️"
        else:
            self.test_results["overall_status"] = "FAIL"
            status_emoji = "❌"
        
        print(f"{status_emoji} Overall Status: {self.test_results['overall_status']}")
        print(f"📊 Security Levels Tested: {successful_levels}/{total_levels}")
        print(f"🔒 One-Time Key Enforcement: {'✅ WORKING' if security_violations == 0 else '❌ VIOLATIONS FOUND'}")
        
        # QuMail exclusivity summary
        exclusivity = self.test_results.get("qumail_exclusivity_tests", {})
        if exclusivity.get("looks_like_gibberish") and exclusivity.get("qumail_decryption_works"):
            print(f"🎭 QuMail Exclusivity: ✅ WORKING (appears as gibberish to non-QuMail apps)")
        else:
            print(f"🎭 QuMail Exclusivity: ❌ FAILED")
        
        # Performance summary
        perf_good = all(
            level_data.get("acceptable", False) 
            for level_data in self.test_results.get("performance_tests", {}).values()
        )
        print(f"⚡ Performance: {'✅ ACCEPTABLE' if perf_good else '⚠️ NEEDS IMPROVEMENT'}")
        
        # Security violations
        if security_violations > 0:
            print(f"\n⚠️ SECURITY VIOLATIONS DETECTED:")
            for violation in self.test_results["security_violations"]:
                print(f"  - {violation['type']}: {violation.get('severity', 'UNKNOWN')}")
        
        # Recommendations
        recommendations = []
        
        if successful_levels < total_levels:
            recommendations.append("Fix key generation for failed security levels")
        
        if security_violations > 0:
            recommendations.append("Address security violations before production use")
        
        if not perf_good:
            recommendations.append("Optimize performance for better key generation times")
        
        if not exclusivity.get("looks_like_gibberish"):
            recommendations.append("Improve encryption format to better hide content from non-QuMail apps")
        
        self.test_results["recommendations"] = recommendations
        
        if recommendations:
            print(f"\n💡 RECOMMENDATIONS:")
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec}")
        else:
            print(f"\n🎉 NO RECOMMENDATIONS - SYSTEM READY FOR PRODUCTION!")

async def main():
    """Main validation runner"""
    validator = QuMailSecurityValidator()
    
    try:
        results = await validator.run_comprehensive_validation()
        
        # Save results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"qumail_security_validation_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📁 Full results saved to: {results_file}")
        
        return results["overall_status"] == "PASS"
        
    except Exception as e:
        print(f"\n❌ VALIDATION FAILED: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)