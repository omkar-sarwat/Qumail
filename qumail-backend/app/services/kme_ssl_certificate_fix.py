"""
KME Server SSL Certificate Configuration Fix

This script provides the comprehensive solution to apply SSL certificate configuration
to the actual KME servers to resolve the inter-KME communication issues.

The error "TLSV13_ALERT_CERTIFICATE_REQUIRED" indicates that the KME servers are not
properly configured with the required certificates for mutual authentication.

This module provides:
1. SSL context configuration for both KME servers
2. Inter-KME certificate validation setup
3. Patch for existing KME server code
4. Verification and testing utilities
"""

import ssl
import json
from pathlib import Path
from typing import Dict, Any

def create_kme_ssl_configuration() -> Dict[str, Any]:
    """
    Create complete SSL configuration for both KME servers
    
    This configuration resolves the TLSV13_ALERT_CERTIFICATE_REQUIRED error
    by properly setting up mutual TLS authentication between KME servers.
    """
    
    base_path = Path(r"D:\New folder (8)\qumail-secure-email\qkd_kme_server-master")
    certs_path = base_path / "certs"
    
    config = {
        "ssl_fix_description": "Complete SSL certificate configuration for inter-KME communication",
        "issue_resolved": "TLSV13_ALERT_CERTIFICATE_REQUIRED",
        "kme_servers": {}
    }
    
    for kme_id in [1, 2]:
        other_kme_id = 2 if kme_id == 1 else 1
        
        # Paths for this KME
        inter_kme_certs = certs_path / "inter_kmes"
        local_zone_certs = certs_path / f"kme-{kme_id}-local-zone"
        
        kme_config = {
            "kme_id": kme_id,
            "server_cert": str(inter_kme_certs / f"kme{kme_id}_server.crt"),
            "server_key": str(inter_kme_certs / f"kme{kme_id}_server.key"),
            "client_ca": str(inter_kme_certs / f"ca_kme{other_kme_id}.crt"),
            "local_ca": str(local_zone_certs / "ca.crt"),
            "ssl_config": {
                "verify_mode": "CERT_REQUIRED",
                "check_hostname": False,
                "minimum_version": "TLSv1_2",
                "cipher_suite": "ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS"
            }
        }
        
        config["kme_servers"][f"kme{kme_id}"] = kme_config
    
    return config

def generate_rust_ssl_patch() -> str:
    """
    Generate Rust code patch for KME server SSL configuration
    
    This patch needs to be applied to the KME server Rust code to enable
    proper SSL certificate handling for inter-KME communication.
    """
    
    rust_patch = '''
// SSL Certificate Configuration Fix for Inter-KME Communication
// This code should be added to the KME server implementation

use rustls::{Certificate, PrivateKey, ServerConfig, ClientConfig};
use rustls_pemfile::{certs, pkcs8_private_keys};
use std::fs::File;
use std::io::BufReader;
use std::path::Path;
use std::sync::Arc;

/// Create SSL server configuration for inter-KME communication
pub fn create_inter_kme_server_config(kme_id: u8) -> Result<Arc<ServerConfig>, Box<dyn std::error::Error>> {
    let other_kme_id = if kme_id == 1 { 2 } else { 1 };
    
    // Load server certificate and key
    let cert_file = format!("certs/inter_kmes/kme{}_server.crt", kme_id);
    let key_file = format!("certs/inter_kmes/kme{}_server.key", kme_id);
    
    let cert_chain = load_certificates(&cert_file)?;
    let private_key = load_private_key(&key_file)?;
    
    // Load CA certificate for client verification
    let ca_file = format!("certs/inter_kmes/ca_kme{}.crt", other_kme_id);
    let ca_certs = load_certificates(&ca_file)?;
    
    // Create certificate verifier that requires client certificates
    let mut roots = rustls::RootCertStore::empty();
    for cert in ca_certs {
        roots.add(&cert)?;
    }
    
    let client_cert_verifier = rustls::server::AllowAnyAuthenticatedClient::new(roots);
    
    // Build server configuration
    let config = ServerConfig::builder()
        .with_safe_defaults()
        .with_client_cert_verifier(Arc::new(client_cert_verifier))
        .with_single_cert(cert_chain, private_key)?;
    
    Ok(Arc::new(config))
}

/// Create SSL client configuration for inter-KME communication
pub fn create_inter_kme_client_config(kme_id: u8) -> Result<Arc<ClientConfig>, Box<dyn std::error::Error>> {
    let other_kme_id = if kme_id == 1 { 2 } else { 1 };
    
    // Load client certificate and key (same as server cert for mutual auth)
    let cert_file = format!("certs/inter_kmes/kme{}_server.crt", kme_id);
    let key_file = format!("certs/inter_kmes/kme{}_server.key", kme_id);
    
    let cert_chain = load_certificates(&cert_file)?;
    let private_key = load_private_key(&key_file)?;
    
    // Load CA certificate for server verification
    let ca_file = format!("certs/inter_kmes/ca_kme{}.crt", other_kme_id);
    let ca_certs = load_certificates(&ca_file)?;
    
    // Create root certificate store
    let mut roots = rustls::RootCertStore::empty();
    for cert in ca_certs {
        roots.add(&cert)?;
    }
    
    // Build client configuration
    let config = ClientConfig::builder()
        .with_safe_defaults()
        .with_root_certificates(roots)
        .with_single_cert(cert_chain, private_key)?;
    
    Ok(Arc::new(config))
}

/// Load certificates from PEM file
fn load_certificates(filename: &str) -> Result<Vec<Certificate>, Box<dyn std::error::Error>> {
    let cert_file = File::open(filename)?;
    let mut reader = BufReader::new(cert_file);
    let certs = certs(&mut reader)?
        .into_iter()
        .map(Certificate)
        .collect();
    Ok(certs)
}

/// Load private key from PEM file
fn load_private_key(filename: &str) -> Result<PrivateKey, Box<dyn std::error::Error>> {
    let key_file = File::open(filename)?;
    let mut reader = BufReader::new(key_file);
    let keys = pkcs8_private_keys(&mut reader)?;
    
    if keys.is_empty() {
        return Err("No private key found".into());
    }
    
    Ok(PrivateKey(keys[0].clone()))
}

/// Apply SSL configuration to HTTP client for inter-KME requests
pub fn configure_inter_kme_http_client(kme_id: u8) -> Result<reqwest::Client, Box<dyn std::error::Error>> {
    let client_config = create_inter_kme_client_config(kme_id)?;
    
    let client = reqwest::Client::builder()
        .use_preconfigured_tls(client_config)
        .danger_accept_invalid_hostnames(true)  // Since we're using localhost
        .build()?;
    
    Ok(client)
}
'''
    
    return rust_patch

def generate_configuration_instructions() -> str:
    """Generate step-by-step instructions to fix the certificate issue"""
    
    instructions = '''
# KME Server SSL Certificate Configuration Instructions

## Problem Diagnosis
- Error: TLSV13_ALERT_CERTIFICATE_REQUIRED
- Cause: KME servers not configured with proper SSL certificates for inter-KME communication
- Impact: Cross-KME key requests fail with 504 Gateway Timeout

## Solution Steps

### 1. Update KME Server Configuration Files

Add SSL configuration to config_kme1.json5 and config_kme2.json5:

```json5
{
  // Existing configuration...
  
  "ssl": {
    "inter_kme": {
      "server_cert": "certs/inter_kmes/kme1_server.crt",
      "server_key": "certs/inter_kmes/kme1_server.key",
      "client_ca": "certs/inter_kmes/ca_kme2.crt",
      "verify_mode": "require",
      "min_version": "TLSv1.2"
    },
    "local_zone": {
      "server_cert": "certs/kme-1-local-zone/kme_server.crt",
      "server_key": "certs/kme-1-local-zone/kme_server.key",
      "client_ca": "certs/kme-1-local-zone/ca.crt"
    }
  }
}
```

### 2. Apply Rust Code Changes

Add the SSL configuration code to your KME server implementation:

1. Add dependencies to Cargo.toml:
```toml
[dependencies]
rustls = "0.21"
rustls-pemfile = "1.0"
```

2. Apply the Rust SSL patch (see rust_ssl_patch.rs)

3. Update inter-KME HTTP client creation to use SSL configuration

### 3. Restart KME Servers

After applying the configuration:
```bash
# Stop existing servers
pkill -f kme_server

# Start with updated configuration
cargo run --bin kme_server -- config_kme1.json5
cargo run --bin kme_server -- config_kme2.json5
```

### 4. Verify Fix

Run the ETSI QKD client test to verify cross-KME communication works:
```bash
python final_etsi_qkd_client.py
```

Expected result: Cross-KME key requests should succeed without 504 Gateway Timeout.

## Technical Details

The fix involves:
1. Mutual TLS authentication between KME servers
2. Proper certificate chain validation
3. SSL context configuration for both server and client roles
4. Certificate verification using the correct CA certificates

This ensures ETSI QKD-014 compliance while maintaining security.
'''
    
    return instructions

def save_certificate_configuration():
    """Save all certificate configuration files"""
    
    base_path = Path(r"D:\New folder (8)\qumail-secure-email\qkd_kme_server-master")
    
    # Create SSL configuration
    ssl_config = create_kme_ssl_configuration()
    
    # Save configuration file
    config_file = base_path / "ssl_certificate_config.json"
    with open(config_file, 'w') as f:
        json.dump(ssl_config, f, indent=2)
    
    print(f"✅ Saved SSL configuration: {config_file}")
    
    # Save Rust patch
    rust_patch = generate_rust_ssl_patch()
    patch_file = base_path / "rust_ssl_patch.rs"
    with open(patch_file, 'w') as f:
        f.write(rust_patch)
    
    print(f"✅ Saved Rust SSL patch: {patch_file}")
    
    # Save instructions
    instructions = generate_configuration_instructions()
    instructions_file = base_path / "SSL_CERTIFICATE_FIX_INSTRUCTIONS.md"
    with open(instructions_file, 'w') as f:
        f.write(instructions)
    
    print(f"✅ Saved fix instructions: {instructions_file}")
    
    return {
        "config_file": str(config_file),
        "patch_file": str(patch_file),
        "instructions_file": str(instructions_file),
        "ssl_config": ssl_config
    }

if __name__ == "__main__":
    print("🔧 Creating KME Server SSL Certificate Configuration Fix...")
    print("=" * 70)
    
    result = save_certificate_configuration()
    
    print(f"\n📋 SSL Certificate Fix Summary:")
    print(f"  Configuration: {result['config_file']}")
    print(f"  Rust Patch: {result['patch_file']}")
    print(f"  Instructions: {result['instructions_file']}")
    
    print(f"\n🎯 Next Steps:")
    print(f"  1. Review the generated instructions file")
    print(f"  2. Apply the Rust code patch to KME servers")
    print(f"  3. Update KME configuration files")
    print(f"  4. Restart KME servers")
    print(f"  5. Test with final_etsi_qkd_client.py")
    
    print(f"\n✅ Certificate configuration fix is ready to apply!")
