# QuMail Configuration Documentation

This document provides an overview of the configuration options for the QuMail Secure Email system.

## Environment Variables

QuMail uses environment variables for configuration. These can be set in a `.env` file in the root directory of the project.

### Core Settings

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `APP_ENV` | Application environment (development, testing, production) | `development` | No |
| `APP_VERSION` | Application version | `0.1.0` | No |
| `DEBUG` | Enable debug mode | `False` | No |
| `SECRET_KEY` | Secret key for securing the application | - | Yes |
| `ALLOWED_ORIGINS` | CORS allowed origins, comma-separated | `http://localhost:3000` | No |

### Database Settings

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DATABASE_URL` | Database connection URL | `sqlite+aiosqlite:///./qumail.db` | No |
| `DATABASE_ECHO` | Echo SQL statements for debugging | `False` | No |

### Google OAuth Settings

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GOOGLE_CLIENT_ID` | Google OAuth client ID | - | Yes |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret | - | Yes |
| `GOOGLE_REDIRECT_URI` | Google OAuth redirect URI | `http://localhost:8000/api/v1/auth/google/callback` | No |

### Quantum Key Management (KME) Settings

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `KME1_HOST` | KME1 server hostname | `localhost` | No |
| `KME1_PORT` | KME1 server port | `8080` | No |
| `KME1_CERT_PATH` | Path to KME1 client certificate | `./certs/kme-1-local-zone/client_1.crt` | No |
| `KME1_KEY_PATH` | Path to KME1 client key | `./certs/kme-1-local-zone/client_1.key` | No |
| `KME1_CA_PATH` | Path to KME1 CA certificate | `./certs/kme-1-local-zone/ca.crt` | No |
| `KME2_HOST` | KME2 server hostname | `localhost` | No |
| `KME2_PORT` | KME2 server port | `8081` | No |
| `KME2_CERT_PATH` | Path to KME2 client certificate | `./certs/kme-2-local-zone/client_3.crt` | No |
| `KME2_KEY_PATH` | Path to KME2 client key | `./certs/kme-2-local-zone/client_3.key` | No |
| `KME2_CA_PATH` | Path to KME2 CA certificate | `./certs/kme-2-local-zone/ca.crt` | No |

### Security Settings

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token expiration in minutes | `30` | No |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token expiration in days | `7` | No |
| `SECURITY_AUDIT_LEVEL` | Security audit logging level (minimal, standard, verbose) | `standard` | No |
| `SECURITY_BREACH_NOTIFY_EMAIL` | Email to notify on security breaches | - | No |

## Configuration Files

### KME Server Configuration

KME server configuration files are in JSON5 format. Example configuration files:

- `config_kme1.json5` - Configuration for KME1 server
- `config_kme2.json5` - Configuration for KME2 server

Example KME configuration:

```json5
{
  // Server configuration
  "server": {
    "bind_address": "0.0.0.0",
    "bind_port": 8080,
    "tls": {
      "cert_path": "./certs/kme-1-local-zone/kme_server.crt",
      "key_path": "./certs/kme-1-local-zone/kme_server.key",
      "ca_path": "./certs/kme-1-local-zone/ca.crt"
    }
  },
  
  // SAE (Security Association Endpoint) configuration
  "sae": {
    "id": "kme-1-1",
    "local_master": true,
    "raw_key_dir": "./raw_keys/kme-1-1"
  },
  
  // Remote KME configuration
  "remote_kmes": [
    {
      "id": "kme-2-2",
      "host": "localhost",
      "port": 8081,
      "tls": {
        "cert_path": "./certs/inter_kmes/kme1-to-kme2.pem",
        "key_path": "./certs/inter_kmes/kme1-to-kme2.key",
        "ca_path": "./certs/inter_kmes/ca_kme2.crt"
      }
    }
  ],
  
  // Database configuration
  "database": {
    "type": "sqlite",
    "path": "./kme1.db"
  }
}
```

## SSL Certificates

SSL certificates are required for secure communication between components:

- `certs/kme-1-local-zone/` - Certificates for KME1 local zone
- `certs/kme-2-local-zone/` - Certificates for KME2 local zone
- `certs/inter_kmes/` - Certificates for inter-KME communication

## Raw Keys

Raw keys are stored in the `raw_keys` directory:

- `raw_keys/kme-1-1/` - Raw keys for KME1 SAE 1
- `raw_keys/kme-1-2/` - Raw keys for KME1 SAE 2
- `raw_keys/kme-2-2/` - Raw keys for KME2 SAE 2

## Quantum Encryption Levels

QuMail supports multiple levels of encryption security:

1. **Level 1: Quantum One-Time Pad (Perfect Secrecy)**
   - Uses quantum keys for perfect secrecy
   - Maximum security, larger message size

2. **Level 2: Quantum-Enhanced AES-256-GCM**
   - Uses quantum random keys with AES-256-GCM
   - High security with efficient encryption

3. **Level 3: Post-Quantum Cryptography**
   - Uses CRYSTALS-Kyber and CRYSTALS-Dilithium
   - Resistant to quantum computer attacks

4. **Level 4: Standard RSA-4096 with AES-256-GCM**
   - Traditional encryption for compatibility
   - Lower security level but widely compatible