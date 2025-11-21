# QuMail KM Testing Guide

## Starting and Testing QKD KME Servers

### Starting the KME Servers

1. Start KME 1 (Alice's Key Management Server):

```powershell
cd "D:\New folder (8)\qumail-secure-email\qkd_kme_server-master"
cargo run --release -- --config config_kme1.json5
```

2. Start KME 2 (Bob's Key Management Server):

```powershell
cd "D:\New folder (8)\qumail-secure-email\qkd_kme_server-master"
cargo run --release -- --config config_kme2.json5
```

3. Start the QuMail Backend Server:

```powershell
cd "D:\New folder (8)\qumail-secure-email\qumail-backend"
uvicorn main:app --reload
```

### Setup Python Path

Before running any tests, make sure Python can find the `app` module by adding the project root to the Python path:

```powershell
# PowerShell
$env:PYTHONPATH = "D:\New folder (8)\qumail-secure-email\qumail-backend"
```

### Testing KME Server Connectivity

We provide multiple test scripts to validate the KM server connectivity:

1. **Basic Connection Test**: Tests only the working endpoints and raw key fallback mechanism:

```powershell
cd "D:\New folder (8)\qumail-secure-email\qumail-backend"
python -m tests.test_working_km
```

This script tests the direct connection to KM servers using proper certificate authentication.

2. **Full Optimized Client Test**: Tests all functionalities of the optimized KM client (may have failures with POST requests):

```powershell
cd "D:\New folder (8)\qumail-secure-email\qumail-backend"
python test_real_km_optimized.py
```

3. **Unit Tests**: Run automated unit tests for all encryption levels:

```powershell
cd "D:\New folder (8)\qumail-secure-email\qumail-backend"
pytest -xvs tests\test_optimized_km_all_levels.py
```

## IDE Setup

For better IDE support with Pylance:

1. The `.vscode/settings.json` file has been configured to add the workspace folder to the Python path
2. The import statements in the code have been updated to use absolute imports

## Known Issues and Workarounds

### Inter-KME Communication Issue

The KME servers have an issue with their inter-KME communication, resulting in 504 Gateway Timeout errors when trying to request encryption keys. This affects the `/api/v1/keys/{slave_sae_id}/enc_keys` endpoint.

**Error from KME logs:**
```
2025-10-04T18:00:05.143Z ERROR [qkd_kme_server::qkd_manager::key_handler] Error sending HTTP request: error sending request for url (https://localhost:15001/keys/activate)
2025-10-04T18:00:05.143Z ERROR [qkd_kme_server::qkd_manager::key_handler] Error activating key on other KME
```

### Direct KM Client

We now use a direct KM client implementation that connects directly to the KM servers without any fallback mechanisms. This provides a more straightforward integration with real KM servers.

The direct KM client (`app/services/direct_km_client.py`) uses PEM certificates and handles all KM server communication directly. This approach is more aligned with how real applications would integrate with QKD KM servers.

**Workaround:**
1. The `test_working_km.py` script implements a fallback mechanism that uses raw key files from the `raw_keys` directory when KME servers fail to deliver keys via their API.
2. For production use, consider either fixing the inter-KME communication issue or implementing the raw key fallback mechanism.

### Certificate Issues

If you encounter certificate errors:

1. Make sure the correct certificates are being used. The certificate paths are set in `app/services/direct_km_client.py`:
   - For KME 1: `kme-1-local-zone/client_1_cert.pem`, `kme-1-local-zone/client_1.key`, `kme-1-local-zone/ca.crt`
   - For KME 2: `kme-2-local-zone/client_3_cert.pem`, `kme-2-local-zone/client_3.key`, `kme-2-local-zone/ca.crt`

2. The KME servers use mutual TLS authentication. Ensure all certificates are valid and properly configured.

## Troubleshooting

If you encounter other issues:

1. Make sure the KM servers are running and accessible at `https://localhost:13000` (KME 1) and `https://localhost:14000` (KME 2)
2. Verify that the PYTHONPATH is set correctly
3. Check KME server logs for errors
4. Ensure all required Python packages are installed (`pip install -r requirements.txt`)
5. Try using the `test_working_km.py` script which focuses only on working endpoints
6. Examine the raw quantum key files in the `raw_keys` directory to ensure they exist and have sufficient entropy