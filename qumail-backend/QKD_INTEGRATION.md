# QuMail QKD Integration Guide

This document provides instructions for integrating the QuMail secure email system with a Quantum Key Distribution (QKD) Key Management Entity (KME) server that implements the ETSI QKD standards.

## Overview

QuMail uses QKD-based encryption to provide quantum-safe email communication. The system integrates with QKD KME servers that follow ETSI standards for quantum key distribution. The integration allows QuMail to:

1. Retrieve quantum-generated encryption keys from KME servers
2. Use these keys for one-time pad or AES encryption
3. Establish quantum-secured communication channels between email users

## QKD KME Server Requirements

The QKD KME server should implement the following ETSI QKD standards:

- ETSI GS QKD 014: Protocol and data format of REST-based key delivery API
- ETSI GS QKD 004: Application Interface

## Running Tests with QKD KME Servers

### Setup Python Path

Before running any tests, make sure Python can find the `app` module by adding the project root to the Python path:

```powershell
# PowerShell
$env:PYTHONPATH = "D:\New folder (8)\qumail-secure-email\qumail-backend"
```

### Run Tests

Now you can run the tests:

```powershell
cd "D:\New folder (8)\qumail-secure-email\qumail-backend"
pytest -xvs tests\test_optimized_km_all_levels.py
```

### Test KM Server Connectivity

To test connectivity to the QKD KME servers, run the included diagnostic script:

```powershell
cd "D:\New folder (8)\qumail-secure-email\qumail-backend"
python test_qkd_connectivity.py --verbose
```

You can also test a specific KME server:

```powershell
python test_qkd_connectivity.py --kme 1
```

## Certificate Configuration

The system requires client certificates for mutual TLS authentication with the KME servers:

1. Client certificates should be in PFX/PKCS#12 format
2. CA certificates should be available to validate server certificates
3. Certificate files should be placed in the following locations:
   ```
   certs/
   ├── kme-1-local-zone/
   │   ├── ca.crt
   │   ├── client_1.pfx
   │   └── ...
   └── kme-2-local-zone/
       ├── ca.crt
       ├── client_3.pfx
       └── ...
   ```

## Raw Keys Configuration

For fallback and testing purposes, QuMail can use raw quantum key files:

1. Raw key files should be placed in the following directory structure:
   ```
   raw_keys/
   ├── kme-1-1/
   │   └── *.cor
   ├── kme-1-2/
   │   └── *.cor
   ├── kme-2-1/
   │   └── *.cor
   └── kme-2-2/
       └── *.cor
   ```

2. Raw key files should be in `.cor` format (binary correlation data)

## KME Server API Endpoints

The QKD KME server should expose the following endpoints:

- `/` - Root endpoint with server status
- `/api/v1/status` - Status endpoint with key availability information
- `/api/v1/sae/info/me` - Information about the client's SAE
- `/api/v1/keys/{sae_id}/status` - Status of keys available for a specific SAE
- `/api/v1/keys/{sae_id}/enc_keys` - Retrieve encryption keys for a specific SAE
- `/api/v1/keys/{sae_id}/dec_keys` - Retrieve decryption keys using key ID

## Troubleshooting

### Certificate Issues

If you encounter certificate-related errors:

1. Verify that the certificate files exist in the correct locations
2. Check that the certificate password is correct (default: "password")
3. Ensure the CA certificate properly validates the server's certificate
4. Check that the client certificate is authorized on the KME server

You can test certificate validity with:

```
openssl pkcs12 -info -in certs/kme-1-local-zone/client_1.pfx -noout
```

### Connectivity Issues

If you cannot connect to the KME server:

1. Verify that the KME server is running and listening on the configured port
2. Check network connectivity (firewall settings, etc.)
3. Verify that the configured URLs are correct
4. Check that the KME server supports the required API endpoints

### Key Retrieval Issues

If you cannot retrieve keys:

1. Verify that keys are available on the KME server
2. Check that your SAE ID is correctly registered on the KME server
3. Ensure that the KME server has established a quantum link with other KME servers

## Implementation Notes

- The system will automatically try alternative endpoints if the standard ETSI endpoints are not available
- If the KME server is unavailable, the system will fall back to local raw key files
- For debugging, the system can generate test keys if no real quantum keys are available