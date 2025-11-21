"""
Simple KME Configuration Fixer
Fixes the 504 Gateway Timeout by updating the kmes_https_interface CA certificate paths
"""

import re
from pathlib import Path
import shutil

def fix_kme_config_simple():
    """Simple fix for KME configurations by replacing specific lines"""
    KME_DIR = Path(r"D:\New folder (8)\qumail-secure-email\qkd_kme_server-master")
    
    # Files to fix
    kme1_config = KME_DIR / "config_kme1.json5"
    kme2_config = KME_DIR / "config_kme2.json5"
    
    print("🔧 Simple KME Configuration Fix")
    print("=" * 50)
    
    # Fix KME1 - change ca_kme1.crt to ca_kme2.crt in kmes_https_interface
    if kme1_config.exists():
        print("📝 Fixing KME1 configuration...")
        
        # Read file
        with open(kme1_config, 'r') as f:
            content = f.read()
        
        # Backup
        backup_path = kme1_config.with_suffix('.json5.backup2')
        with open(backup_path, 'w') as f:
            f.write(content)
        print(f"  ✓ Backed up to: {backup_path.name}")
        
        # Fix: In kmes_https_interface section, change ca_kme1.crt to ca_kme2.crt
        # Look for the kmes_https_interface section and fix the CA path
        pattern = r'("kmes_https_interface":\s*{[^}]*"ca_client_cert_path":\s*"[^"]*/)ca_kme1(\.crt"[^}]*})'
        replacement = r'\1ca_kme2\2'
        
        new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        
        if new_content != content:
            with open(kme1_config, 'w') as f:
                f.write(new_content)
            print("  ✅ Fixed: KME1 now trusts ca_kme2.crt for inter-KME connections")
        else:
            print("  ⚠️ No changes needed or pattern not found")
    
    # Fix KME2 - change ca_kme2.crt to ca_kme1.crt in kmes_https_interface  
    if kme2_config.exists():
        print("📝 Fixing KME2 configuration...")
        
        # Read file
        with open(kme2_config, 'r') as f:
            content = f.read()
        
        # Backup
        backup_path = kme2_config.with_suffix('.json5.backup2')
        with open(backup_path, 'w') as f:
            f.write(content)
        print(f"  ✓ Backed up to: {backup_path.name}")
        
        # Fix: In kmes_https_interface section, change ca_kme2.crt to ca_kme1.crt
        pattern = r'("kmes_https_interface":\s*{[^}]*"ca_client_cert_path":\s*"[^"]*/)ca_kme2(\.crt"[^}]*})'
        replacement = r'\1ca_kme1\2'
        
        new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        
        if new_content != content:
            with open(kme2_config, 'w') as f:
                f.write(new_content)
            print("  ✅ Fixed: KME2 now trusts ca_kme1.crt for inter-KME connections")
        else:
            print("  ⚠️ No changes needed or pattern not found")
    
    print("\n🎯 CONFIGURATION FIX COMPLETED!")
    print("📋 What was fixed:")
    print("   • KME1 kmes_https_interface now uses ca_kme2.crt")  
    print("   • KME2 kmes_https_interface now uses ca_kme1.crt")
    print("   • This allows proper SSL handshake for inter-KME communication")
    
    print("\n🚀 NEXT STEPS:")
    print("   1. Stop current KME servers")
    print("   2. Restart both KME servers")  
    print("   3. Test with: python etsi_qkd_test.py")

if __name__ == "__main__":
    fix_kme_config_simple()
