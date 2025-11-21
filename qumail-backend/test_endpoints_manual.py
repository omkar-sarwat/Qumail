#!/usr/bin/env python3
"""
Manual endpoint testing script to verify fixes before running full Testsprite tests
"""
import requests
import json

BASE_URL = "http://localhost:8000"
TIMEOUT = 10

def test_root_endpoint():
    """Test TC002: Root endpoint should return 200 with API info"""
    print("\n" + "="*60)
    print("TEST 1: Root Endpoint (TC002)")
    print("="*60)
    try:
        response = requests.get(f"{BASE_URL}/", timeout=TIMEOUT)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ PASS: Got 200 OK")
            print(f"Service: {data.get('service')}")
            print(f"Features: {len(data.get('features', []))} features")
        else:
            print(f"❌ FAIL: Expected 200, got {response.status_code}")
            print(f"Response: {response.text[:200]}")
    except Exception as e:
        print(f"❌ ERROR: {e}")

def test_quantum_status_redirect():
    """Test TC007: Quantum status should redirect with 307"""
    print("\n" + "="*60)
    print("TEST 2: Quantum Status Redirect (TC007)")
    print("="*60)
    try:
        response = requests.get(f"{BASE_URL}/quantum/status", allow_redirects=False, timeout=TIMEOUT)
        print(f"Status Code: {response.status_code}")
        location = response.headers.get("Location", "")
        print(f"Location Header: {location}")
        
        if response.status_code == 307:
            print(f"✅ PASS: Got 307 Temporary Redirect")
            if "quantum_status.html" in location:
                print(f"✅ PASS: Location points to quantum_status.html")
            else:
                print(f"❌ FAIL: Location doesn't point to quantum_status.html")
        else:
            print(f"❌ FAIL: Expected 307, got {response.status_code}")
    except Exception as e:
        print(f"❌ ERROR: {e}")

def test_encryption_status():
    """Test TC005: Encryption status should have correct securityLevels format"""
    print("\n" + "="*60)
    print("TEST 3: Encryption Status (TC005)")
    print("="*60)
    try:
        response = requests.get(f"{BASE_URL}/encryption/status", timeout=TIMEOUT)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            security_levels = data.get("securityLevels", {})
            print(f"Security Levels Keys: {list(security_levels.keys())}")
            
            expected_keys = ["quantum_otp", "quantum_aes", "post_quantum", "standard_rsa"]
            has_all_keys = all(key in security_levels for key in expected_keys)
            
            if has_all_keys:
                print(f"✅ PASS: All expected security level keys present")
                for key in expected_keys:
                    print(f"  - {key}: {security_levels[key][:50]}...")
            else:
                print(f"❌ FAIL: Missing expected keys")
                print(f"Expected: {expected_keys}")
                print(f"Got: {list(security_levels.keys())}")
                
            # Check KME status
            kme_status = data.get("kmeStatus", [])
            print(f"\nKME Status:")
            for kme in kme_status:
                print(f"  - {kme.get('id')}: {kme.get('status')} (latency: {kme.get('latency')}ms)")
        else:
            print(f"❌ FAIL: Expected 200, got {response.status_code}")
    except Exception as e:
        print(f"❌ ERROR: {e}")

def test_health_check():
    """Test TC001: Health check should return 200"""
    print("\n" + "="*60)
    print("TEST 4: Health Check (TC001)")
    print("="*60)
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=TIMEOUT)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ PASS: Got 200 OK")
            print(f"Healthy: {data.get('healthy')}")
            services = data.get('services', {})
            for service, status in services.items():
                print(f"  - {service}: {status}")
        else:
            print(f"❌ FAIL: Expected 200, got {response.status_code}")
    except Exception as e:
        print(f"❌ ERROR: {e}")

def test_generate_keys():
    """Test TC006: Generate quantum keys endpoint"""
    print("\n" + "="*60)
    print("TEST 5: Generate Quantum Keys (TC006)")
    print("="*60)
    try:
        response = requests.post(f"{BASE_URL}/api/v1/quantum/generate-keys?count=5", timeout=TIMEOUT)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ PASS: Got 200 OK")
            print(f"Success: {data.get('success')}")
            print(f"Total Generated: {data.get('total', {}).get('generated')}")
            print(f"Total Successful: {data.get('total', {}).get('successful')}")
            print(f"Success Rate: {data.get('total', {}).get('successRate')}%")
        else:
            print(f"❌ FAIL: Expected 200, got {response.status_code}")
            print(f"Response: {response.text[:200]}")
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("QuMail Backend Manual Endpoint Tests")
    print("Testing fixes before running full Testsprite suite")
    print("="*60)
    
    # Run all tests
    test_health_check()
    test_root_endpoint()
    test_quantum_status_redirect()
    test_encryption_status()
    test_generate_keys()
    
    print("\n" + "="*60)
    print("Manual testing complete!")
    print("="*60)
    print("\nNext steps:")
    print("1. If tests PASS: Run full Testsprite suite")
    print("2. If tests FAIL: Backend needs restart or code has issues")
    print("\nTo restart backend:")
    print("  taskkill /F /IM python.exe /T")
    print("  cd qumail-backend")
    print("  .\\venv\\Scripts\\Activate.ps1")
    print("  python -m uvicorn app.main:app --reload --port 8000")
    print("="*60 + "\n")
