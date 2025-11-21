"""
Fix KME Configuration Files for Inter-KME Communication
Based on ETSI QKD-014 Standard

This script fixes the root cause of the 504 Gateway Timeout issue by properly
configuring the kmes_https_interface section for inter-KME authentication.
"""

import json
try:
    import json5
except ImportError:
    # Fallback to regular json for .json5 files
    json5 = json
from pathlib import Path
import shutil
import os

# Paths
KME_DIR = Path(r"D:\New folder (8)\qumail-secure-email\qkd_kme_server-master")
CERTS_DIR = KME_DIR / "certs" / "inter_kmes"

def backup_config(config_path):
    """Backup existing config file"""
    backup_path = config_path.with_suffix('.json5.backup')
    if config_path.exists() and not backup_path.exists():
        shutil.copy(config_path, backup_path)
        print(f"✓ Backed up: {config_path.name} -> {backup_path.name}")

def verify_certificate_files():
    """Verify all required certificate files exist"""
    print("\n🔍 Verifying certificate files...")
    
    required_files = [
        "ca_kme1.crt",
        "ca_kme2.crt", 
        "kme1_server.crt",
        "kme1_server.key",
        "kme2_server.crt", 
        "kme2_server.key",
        "kme1-to-kme2.pfx",
        "kme2-to-kme1.pfx"
    ]
    
    missing_files = []
    for file_name in required_files:
        file_path = CERTS_DIR / file_name
        if file_path.exists():
            print(f"  ✅ {file_name}")
        else:
            print(f"  ❌ {file_name} (MISSING)")
            missing_files.append(file_name)
    
    if missing_files:
        print(f"\n⚠️  Missing {len(missing_files)} certificate files!")
        return False
    else:
        print(f"\n✅ All {len(required_files)} certificate files found!")
        return True

def fix_kme1_config():
    """Fix KME1 configuration with proper inter-KME SSL settings"""
    config_path = KME_DIR / "config_kme1.json5"
    
    # Backup existing config
    backup_config(config_path)
    
    # Read existing config
    with open(config_path, 'r') as f:
        config = json5.load(f)
    
    # Fix the critical kmes_https_interface section
    print("🔧 Fixing KME1 inter-KME SSL configuration...")
    config["this_kme"]["kmes_https_interface"] = {
        "listen_address": "0.0.0.0:13001",
        "ca_client_cert_path": "certs/inter_kmes/ca_kme2.crt",  # Trust KME2's CA for incoming connections
        "server_cert_path": "certs/inter_kmes/kme1_server.crt",  # KME1's server certificate
        "server_key_path": "certs/inter_kmes/kme1_server.key"    # KME1's private key
    }
    
    # Ensure other_kmes configuration is correct
    for other_kme in config["other_kmes"]:
        if other_kme["id"] == 2:
            other_kme["inter_kme_bind_address"] = "localhost:15001"  # KME2's inter-KME port
            other_kme["https_client_authentication_certificate"] = "certs/inter_kmes/kme1-to-kme2.pfx"
            other_kme["https_client_authentication_certificate_password"] = "password"
    
    # Write fixed config
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Fixed KME1 configuration: {config_path}")
    return config

def fix_kme2_config():
    """Fix KME2 configuration with proper inter-KME SSL settings"""
    config_path = KME_DIR / "config_kme2.json5"
    
    # Backup existing config
    backup_config(config_path)
    
    # Read existing config
    with open(config_path, 'r') as f:
        config = json5.load(f)
    
    # Fix the critical kmes_https_interface section
    print("🔧 Fixing KME2 inter-KME SSL configuration...")
    config["this_kme"]["kmes_https_interface"] = {
        "listen_address": "0.0.0.0:15001",
        "ca_client_cert_path": "certs/inter_kmes/ca_kme1.crt",  # Trust KME1's CA for incoming connections
        "server_cert_path": "certs/inter_kmes/kme2_server.crt",  # KME2's server certificate
        "server_key_path": "certs/inter_kmes/kme2_server.key"    # KME2's private key
    }
    
    # Ensure other_kmes configuration is correct
    for other_kme in config["other_kmes"]:
        if other_kme["id"] == 1:
            other_kme["inter_kme_bind_address"] = "localhost:13001"  # KME1's inter-KME port
            other_kme["https_client_authentication_certificate"] = "certs/inter_kmes/kme2-to-kme1.pfx"
            other_kme["https_client_authentication_certificate_password"] = "password"
    
    # Write fixed config
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Fixed KME2 configuration: {config_path}")
    return config

def validate_config(config, kme_id):
    """Validate the configuration"""
    print(f"\n🔍 Validating KME{kme_id} configuration...")
    
    # Check inter-KME interface
    kmes_interface = config["this_kme"]["kmes_https_interface"]
    
    # Validate certificate paths
    cert_paths = [
        ("Inter-KME CA", kmes_interface["ca_client_cert_path"]),
        ("Server Certificate", kmes_interface["server_cert_path"]),
        ("Server Key", kmes_interface["server_key_path"])
    ]
    
    all_valid = True
    for name, rel_path in cert_paths:
        full_path = KME_DIR / rel_path
        if full_path.exists():
            print(f"  ✅ {name}: {rel_path}")
        else:
            print(f"  ❌ {name}: {rel_path} (NOT FOUND)")
            all_valid = False
    
    # Check client certificates in other_kmes
    for other_kme in config["other_kmes"]:
        cert_path = KME_DIR / other_kme["https_client_authentication_certificate"]
        if cert_path.exists():
            print(f"  ✅ Client cert to KME{other_kme['id']}: {other_kme['https_client_authentication_certificate']}")
        else:
            print(f"  ❌ Client cert to KME{other_kme['id']}: {other_kme['https_client_authentication_certificate']} (NOT FOUND)")
            all_valid = False
    
    return all_valid

def create_restart_script():
    """Create script to restart KME servers with fixed configuration"""
    script_content = '''@echo off
echo ===============================================
echo KME Server Restart Script (Fixed Configuration)
echo ===============================================

echo Stopping any running KME servers...
taskkill /f /im qkd_kme_server.exe 2>nul
timeout /t 2 /nobreak >nul

echo.
echo Starting KME1 with fixed configuration...
cd /d "D:\\New folder (8)\\qumail-secure-email\\qkd_kme_server-master"
start "KME1 Server (Fixed)" cmd /k "cargo run --bin qkd_kme_server -- config_kme1.json5"

echo Waiting 5 seconds...
timeout /t 5 /nobreak >nul

echo.
echo Starting KME2 with fixed configuration...
start "KME2 Server (Fixed)" cmd /k "cargo run --bin qkd_kme_server -- config_kme2.json5"

echo.
echo ===============================================
echo Both KME servers started with fixed SSL config!
echo ===============================================
echo KME1 SAE Interface:      https://localhost:13000
echo KME1 Inter-KME Interface: https://localhost:13001
echo KME2 SAE Interface:      https://localhost:14000  
echo KME2 Inter-KME Interface: https://localhost:15001
echo ===============================================
echo.
echo Wait 10-15 seconds for servers to fully initialize,
echo then test with: python etsi_qkd_test.py
echo.
pause'''
    
    script_path = KME_DIR / "restart_kmes_fixed.bat"
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    print(f"📝 Created restart script: {script_path}")
    return script_path

def main():
    print("=" * 80)
    print("🔧 KME CONFIGURATION FIXER - ETSI QKD-014 Inter-KME SSL Fix")
    print("=" * 80)
    print("This script fixes the 504 Gateway Timeout issue by properly")
    print("configuring inter-KME SSL certificate authentication.")
    print("=" * 80)
    
    # Check if KME directory exists
    if not KME_DIR.exists():
        print(f"❌ KME directory not found: {KME_DIR}")
        return False
    
    print(f"✅ KME directory: {KME_DIR}")
    
    # Verify certificate files
    if not verify_certificate_files():
        print("\n❌ Cannot proceed without required certificate files!")
        return False
    
    # Fix configurations
    print("\n" + "=" * 60)
    print("🔧 FIXING CONFIGURATION FILES")
    print("=" * 60)
    
    try:
        # Fix KME1
        kme1_config = fix_kme1_config()
        kme1_valid = validate_config(kme1_config, 1)
        
        # Fix KME2  
        kme2_config = fix_kme2_config()
        kme2_valid = validate_config(kme2_config, 2)
        
        # Create restart script
        restart_script = create_restart_script()
        
        # Summary
        print("\n" + "=" * 80)
        print("📋 CONFIGURATION FIX SUMMARY")
        print("=" * 80)
        print(f"KME1 Configuration: {'✅ Fixed & Validated' if kme1_valid else '❌ Issues Found'}")
        print(f"KME2 Configuration: {'✅ Fixed & Validated' if kme2_valid else '❌ Issues Found'}")
        
        if kme1_valid and kme2_valid:
            print("\n🎉 CONFIGURATION FIX SUCCESSFUL!")
            print("\n📋 WHAT WAS FIXED:")
            print("  • KME1 now trusts ca_kme2.crt for incoming inter-KME connections")
            print("  • KME2 now trusts ca_kme1.crt for incoming inter-KME connections")
            print("  • Both KMEs use correct server certificates and keys")
            print("  • Client certificate paths verified")
            
            print("\n🚀 NEXT STEPS:")
            print("  1. Run the restart script:")
            print(f"     {restart_script}")
            print("  2. Wait 10-15 seconds for servers to initialize")
            print("  3. Test the fix:")
            print("     python etsi_qkd_test.py")
            
            print("\n🎯 EXPECTED RESULT:")
            print("  ✅ Cross-KME key requests should now work")
            print("  ✅ No more 504 Gateway Timeout errors")
            print("  ✅ Inter-KME SSL handshake success")
            
            return True
        else:
            print("\n❌ CONFIGURATION FIX INCOMPLETE!")
            print("Some certificate files are missing or paths are incorrect.")
            return False
            
    except Exception as e:
        print(f"\n❌ Error fixing configurations: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
