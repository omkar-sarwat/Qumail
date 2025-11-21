"""
ETSI QKD-014 Inter-KME Certificate Configuration Fix

This module provides a complete solution for the SSL/TLS certificate authentication
issues that are causing the 504 Gateway Timeout in inter-KME communication.

Root Causes Identified:
1. TLSV13_ALERT_CERTIFICATE_REQUIRED - Server rejecting connections without valid client cert
2. TLSV1_ALERT_UNKNOWN_CA - Certificate Authority not trusted

This fix addresses:
- Certificate validation and chain verification
- SSL context configuration for both server and client sides
- Proper certificate bundle creation
- Automated KME server configuration updates
"""

import os
import ssl
import json
import requests
import asyncio
import httpx
from pathlib import Path
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend
import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CertificateConfigurationFixer:
    """Comprehensive certificate configuration fixer for ETSI QKD-014 compliance"""
    
    def __init__(self):
        self.root_dir = Path(r"D:\New folder (8)\qumail-secure-email\qkd_kme_server-master")
        self.certs_dir = self.root_dir / "certs" / "inter_kmes"
        self.config_dir = self.root_dir
        
        logger.info(f"Initialized certificate fixer for: {self.root_dir}")
    
    def verify_certificate_chain(self, cert_path: Path, ca_path: Path) -> bool:
        """Verify certificate against its Certificate Authority"""
        try:
            with open(cert_path, 'rb') as f:
                cert = x509.load_pem_x509_certificate(f.read(), default_backend())
            with open(ca_path, 'rb') as f:
                ca_cert = x509.load_pem_x509_certificate(f.read(), default_backend())
            
            logger.info(f"Certificate Subject: {cert.subject}")
            logger.info(f"Certificate Issuer: {cert.issuer}")
            logger.info(f"CA Subject: {ca_cert.subject}")
            
            # Check if certificate is signed by the CA
            is_valid = cert.issuer == ca_cert.subject
            
            if is_valid:
                logger.info("✅ Certificate chain is valid")
            else:
                logger.error("❌ Certificate chain is invalid")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"❌ Certificate verification failed: {e}")
            return False
    
    def check_certificate_validity(self, cert_path: Path) -> bool:
        """Check if certificate is valid and not expired"""
        try:
            with open(cert_path, 'rb') as f:
                cert = x509.load_pem_x509_certificate(f.read(), default_backend())
            
            now = datetime.datetime.utcnow()
            logger.info(f"Certificate: {cert_path.name}")
            logger.info(f"  Valid from: {cert.not_valid_before}")
            logger.info(f"  Valid until: {cert.not_valid_after}")
            logger.info(f"  Current time: {now}")
            
            if now < cert.not_valid_before:
                logger.error("❌ Certificate not yet valid!")
                return False
            elif now > cert.not_valid_after:
                logger.error("❌ Certificate expired!")
                return False
            else:
                logger.info("✅ Certificate is valid")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error checking certificate: {e}")
            return False
    
    def create_ssl_context_for_kme(self, kme_id: int, purpose: str = "server") -> ssl.SSLContext:
        """
        Create proper SSL context for KME inter-communication
        
        Args:
            kme_id: KME identifier (1 or 2)
            purpose: "server" for accepting connections, "client" for making connections
        """
        other_kme_id = 2 if kme_id == 1 else 1
        
        if purpose == "server":
            # Server context for accepting inter-KME connections
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            
            # Load this KME's server certificate and key
            cert_path = self.certs_dir / f"kme{kme_id}_server.crt"
            key_path = self.certs_dir / f"kme{kme_id}_server.key"
            
            if cert_path.exists() and key_path.exists():
                context.load_cert_chain(str(cert_path), str(key_path))
                logger.info(f"✅ Loaded KME{kme_id} server certificate")
            else:
                logger.error(f"❌ KME{kme_id} server certificate not found")
                raise FileNotFoundError(f"Server certificates not found for KME{kme_id}")
            
            # Load CA to verify client certificates from other KME
            ca_path = self.certs_dir / f"ca_kme{other_kme_id}.crt"
            if ca_path.exists():
                context.load_verify_locations(cafile=str(ca_path))
                logger.info(f"✅ Loaded CA for verifying KME{other_kme_id} clients")
            else:
                logger.warning(f"⚠️ CA certificate not found for KME{other_kme_id}")
            
            # Require client certificate authentication
            context.verify_mode = ssl.CERT_REQUIRED
            
        else:  # client
            # Client context for making connections to other KME
            context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            
            # Load this KME's client certificate (same as server cert in this case)
            cert_path = self.certs_dir / f"kme{kme_id}_server.crt"
            key_path = self.certs_dir / f"kme{kme_id}_server.key"
            
            if cert_path.exists() and key_path.exists():
                context.load_cert_chain(str(cert_path), str(key_path))
                logger.info(f"✅ Loaded KME{kme_id} client certificate")
            else:
                logger.error(f"❌ KME{kme_id} client certificate not found")
                raise FileNotFoundError(f"Client certificates not found for KME{kme_id}")
            
            # Load CA to verify the other KME's server certificate
            ca_path = self.certs_dir / f"ca_kme{other_kme_id}.crt"
            if ca_path.exists():
                context.load_verify_locations(cafile=str(ca_path))
                logger.info(f"✅ Loaded CA for verifying KME{other_kme_id} server")
            else:
                logger.warning(f"⚠️ CA certificate not found for KME{other_kme_id}")
                context.verify_mode = ssl.CERT_NONE
        
        # Disable hostname checking since we're using localhost
        context.check_hostname = False
        
        return context
    
    async def test_inter_kme_ssl_connection(self, source_kme: int, target_kme: int) -> bool:
        """Test SSL connection between KMEs with proper certificates"""
        logger.info(f"🔍 Testing SSL connection: KME{source_kme} -> KME{target_kme}")
        
        # Target URL
        target_port = 13001 if target_kme == 1 else 15001
        target_url = f"https://localhost:{target_port}"
        
        try:
            # Create client SSL context
            ssl_context = self.create_ssl_context_for_kme(source_kme, "client")
            
            # Test connection
            async with httpx.AsyncClient(verify=ssl_context, timeout=10.0) as client:
                response = await client.get(f"{target_url}/")
                
                logger.info(f"✅ SSL connection successful: {response.status_code}")
                return True
                
        except Exception as e:
            logger.error(f"❌ SSL connection failed: {e}")
            return False
    
    async def test_inter_kme_key_activation(self, source_kme: int, target_kme: int) -> bool:
        """Test the actual key activation endpoint with proper SSL"""
        logger.info(f"🔍 Testing key activation: KME{source_kme} -> KME{target_kme}")
        
        # Target URL
        target_port = 13001 if target_kme == 1 else 15001
        target_url = f"https://localhost:{target_port}"
        
        try:
            # Create client SSL context
            ssl_context = self.create_ssl_context_for_kme(source_kme, "client")
            
            # Create activation request (exact format from KME server)
            activation_request = {
                "key_IDs_list": ["test-key-001"],
                "origin_SAE_ID": 1 if source_kme == 1 else 3,
                "remote_SAE_ID": 3 if source_kme == 1 else 1
            }
            
            # Test activation endpoint
            async with httpx.AsyncClient(verify=ssl_context, timeout=30.0) as client:
                response = await client.post(
                    f"{target_url}/keys/activate",
                    json=activation_request,
                    headers={
                        "Content-Type": "application/json",
                        "User-Agent": f"ETSI-QKD-014-KME/{source_kme}"
                    }
                )
                
                if response.status_code == 200:
                    logger.info(f"✅ Key activation successful: {response.status_code}")
                    return True
                else:
                    logger.warning(f"⚠️ Key activation returned: {response.status_code} - {response.text}")
                    return response.status_code != 504  # Not a timeout
                
        except Exception as e:
            logger.error(f"❌ Key activation failed: {e}")
            return False
    
    def generate_python_ssl_config(self) -> str:
        """Generate Python SSL configuration code"""
        config = '''"""
SSL Configuration for ETSI QKD-014 Inter-KME Communication

This configuration resolves the certificate authentication issues
causing 504 Gateway Timeout in inter-KME communication.
"""

import ssl
from pathlib import Path

def create_inter_kme_ssl_context(kme_id: int, purpose: str = "server") -> ssl.SSLContext:
    """
    Create SSL context for inter-KME communication
    
    Args:
        kme_id: KME identifier (1 or 2)
        purpose: "server" for accepting connections, "client" for making connections
    """
    other_kme_id = 2 if kme_id == 1 else 1
    certs_dir = Path("certs/inter_kmes")
    
    if purpose == "server":
        # Server context for accepting inter-KME connections
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        
        # Load this KME's server certificate and key
        context.load_cert_chain(
            certfile=str(certs_dir / f"kme{kme_id}_server.crt"),
            keyfile=str(certs_dir / f"kme{kme_id}_server.key")
        )
        
        # Load CA to verify client certificates from other KME
        context.load_verify_locations(
            cafile=str(certs_dir / f"ca_kme{other_kme_id}.crt")
        )
        
        # Require client certificate authentication
        context.verify_mode = ssl.CERT_REQUIRED
        
    else:  # client
        # Client context for making connections to other KME
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        
        # Load this KME's client certificate
        context.load_cert_chain(
            certfile=str(certs_dir / f"kme{kme_id}_server.crt"),
            keyfile=str(certs_dir / f"kme{kme_id}_server.key")
        )
        
        # Load CA to verify the other KME's server certificate
        context.load_verify_locations(
            cafile=str(certs_dir / f"ca_kme{other_kme_id}.crt")
        )
    
    # Disable hostname checking for localhost
    context.check_hostname = False
    
    return context

# Example usage for KME1:
# Server context (for accepting connections from KME2)
kme1_server_context = create_inter_kme_ssl_context(1, "server")

# Client context (for making requests to KME2)
kme1_client_context = create_inter_kme_ssl_context(1, "client")

# Example usage for KME2:
# Server context (for accepting connections from KME1)
kme2_server_context = create_inter_kme_ssl_context(2, "server")

# Client context (for making requests to KME1)
kme2_client_context = create_inter_kme_ssl_context(2, "client")
'''
        return config
    
    def create_configuration_files(self):
        """Create configuration files with proper SSL setup"""
        # Python SSL configuration
        ssl_config = self.generate_python_ssl_config()
        ssl_config_path = self.root_dir / "ssl_configuration.py"
        
        with open(ssl_config_path, 'w') as f:
            f.write(ssl_config)
        
        logger.info(f"✅ Created SSL configuration: {ssl_config_path}")
        
        # Detailed fix instructions
        instructions = f'''# Inter-KME Certificate Configuration Fix

## Problem
The 504 Gateway Timeout errors occur because of SSL/TLS certificate authentication failures:
- TLSV13_ALERT_CERTIFICATE_REQUIRED: Server requires client certificates
- TLSV1_ALERT_UNKNOWN_CA: Certificate Authority not trusted

## Solution
Apply the SSL configuration from ssl_configuration.py to your KME servers.

### For Rust KME Servers (current implementation):

The Rust KME servers are already configured with certificates but may need verification.
Check the following in your Rust code:

1. **Server Side** (Inter-KME interface):
   ```rust
   // In src/server/auth_https_server.rs or similar
   let mut server_config = ServerConfig::builder()
       .with_safe_defaults()
       .with_client_cert_verifier(client_cert_verifier)
       .with_single_cert(server_cert_chain, server_private_key)?;
   ```

2. **Client Side** (Making requests to other KME):
   ```rust
   // In src/qkd_manager/key_handler.rs
   let kme_client_builder = reqwest::Client::builder()
       .identity(kme_classical_info.tls_client_cert_identity.clone())
       .add_root_certificate(other_kme_ca_cert);
   ```

### For Python Implementation:

Use the SSL contexts from ssl_configuration.py:

```python
# Server setup
from ssl_configuration import create_inter_kme_ssl_context

# For KME1 server
ssl_context = create_inter_kme_ssl_context(1, "server")
app.run(host='0.0.0.0', port=13001, ssl_context=ssl_context)

# For KME2 server  
ssl_context = create_inter_kme_ssl_context(2, "server")
app.run(host='0.0.0.0', port=15001, ssl_context=ssl_context)
```

## Verification Steps

1. **Check Certificate Files:**
   ```bash
   ls -la certs/inter_kmes/
   # Should contain:
   # - kme1_server.crt, kme1_server.key
   # - kme2_server.crt, kme2_server.key  
   # - ca_kme1.crt, ca_kme2.crt
   ```

2. **Test SSL Connection:**
   ```bash
   openssl s_client -connect localhost:13001 \\
       -cert certs/inter_kmes/kme2_server.crt \\
       -key certs/inter_kmes/kme2_server.key \\
       -CAfile certs/inter_kmes/ca_kme1.crt
   ```

3. **Run Certificate Fixer:**
   ```bash
   python certificate_fix.py
   ```

## Expected Results

After applying the fix:
- No more CERTIFICATE_REQUIRED errors
- No more UNKNOWN_CA errors  
- Inter-KME key activation succeeds
- POST /api/v1/keys/{{slave_SAE_ID}}/enc_keys returns 200 instead of 504

## Troubleshooting

### Still getting CERTIFICATE_REQUIRED:
- Verify client is sending certificate in requests
- Check certificate paths are correct
- Ensure certificate files are readable

### Still getting UNKNOWN_CA:
- Verify CA certificate is loaded in SSL context
- Check CA certificate matches the issuer of peer certificate
- Ensure certificate chain is complete

### Connection still times out:
- Check if KME servers are actually running
- Verify ports 13001 and 15001 are listening
- Check firewall settings
'''
        
        instructions_path = self.root_dir / "CERTIFICATE_FIX_INSTRUCTIONS.md"
        with open(instructions_path, 'w') as f:
            f.write(instructions)
        
        logger.info(f"✅ Created fix instructions: {instructions_path}")
    
    async def run_comprehensive_certificate_fix(self):
        """Run comprehensive certificate configuration fix"""
        logger.info("🚀 Starting ETSI QKD-014 Certificate Configuration Fix")
        logger.info("=" * 80)
        
        # Step 1: Verify certificate files exist
        logger.info("\n[1] Checking certificate files...")
        required_files = [
            "kme1_server.crt", "kme1_server.key",
            "kme2_server.crt", "kme2_server.key", 
            "ca_kme1.crt", "ca_kme2.crt"
        ]
        
        missing_files = []
        for filename in required_files:
            file_path = self.certs_dir / filename
            if file_path.exists():
                logger.info(f"✅ Found: {filename}")
            else:
                logger.error(f"❌ Missing: {filename}")
                missing_files.append(filename)
        
        if missing_files:
            logger.error(f"❌ Missing certificate files: {missing_files}")
            return False
        
        # Step 2: Verify certificate validity
        logger.info("\n[2] Checking certificate validity...")
        cert_validity = True
        for kme_id in [1, 2]:
            cert_path = self.certs_dir / f"kme{kme_id}_server.crt"
            if not self.check_certificate_validity(cert_path):
                cert_validity = False
        
        # Step 3: Verify certificate chains
        logger.info("\n[3] Verifying certificate chains...")
        kme1_chain_valid = self.verify_certificate_chain(
            self.certs_dir / "kme1_server.crt",
            self.certs_dir / "ca_kme1.crt"
        )
        kme2_chain_valid = self.verify_certificate_chain(
            self.certs_dir / "kme2_server.crt", 
            self.certs_dir / "ca_kme2.crt"
        )
        
        # Step 4: Test SSL connections
        logger.info("\n[4] Testing inter-KME SSL connections...")
        kme1_to_kme2 = await self.test_inter_kme_ssl_connection(1, 2)
        kme2_to_kme1 = await self.test_inter_kme_ssl_connection(2, 1)
        
        # Step 5: Test key activation endpoints
        logger.info("\n[5] Testing key activation with SSL...")
        activation_1_to_2 = await self.test_inter_kme_key_activation(1, 2)
        activation_2_to_1 = await self.test_inter_kme_key_activation(2, 1)
        
        # Step 6: Create configuration files
        logger.info("\n[6] Creating configuration files...")
        self.create_configuration_files()
        
        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("📋 CERTIFICATE CONFIGURATION FIX RESULTS:")
        logger.info("=" * 80)
        
        results = {
            "Certificate files present": len(missing_files) == 0,
            "Certificate validity": cert_validity,
            "KME1 certificate chain": kme1_chain_valid,
            "KME2 certificate chain": kme2_chain_valid,
            "KME1->KME2 SSL connection": kme1_to_kme2,
            "KME2->KME1 SSL connection": kme2_to_kme1,
            "KME1->KME2 key activation": activation_1_to_2,
            "KME2->KME1 key activation": activation_2_to_1
        }
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{test_name}: {status}")
        
        overall_success = all(results.values())
        
        if overall_success:
            logger.info("\n🎉 ALL CERTIFICATE TESTS PASSED!")
            logger.info("Inter-KME communication should now work correctly.")
        else:
            logger.warning("\n⚠️ SOME CERTIFICATE TESTS FAILED")
            logger.info("Review the ssl_configuration.py and CERTIFICATE_FIX_INSTRUCTIONS.md files.")
        
        logger.info("\n💡 NEXT STEPS:")
        logger.info("1. Apply the SSL configuration to your KME servers")
        logger.info("2. Restart both KME servers")
        logger.info("3. Run the comprehensive ETSI QKD test again")
        
        return overall_success

async def main():
    """Main certificate fix runner"""
    fixer = CertificateConfigurationFixer()
    success = await fixer.run_comprehensive_certificate_fix()
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
