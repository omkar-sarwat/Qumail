# QuMail Quantum Status Dashboard

The Quantum Status Dashboard provides real-time monitoring of the quantum encryption system powering QuMail's secure email platform.

## Features

- **Real-time Status Monitoring**: View the operational status of the quantum key distribution system
- **KME Server Information**: Monitor key management entity servers and their available keys
- **Encryption Statistics**: Track quantum-encrypted emails and encryption levels
- **Key Usage Charts**: Visualize quantum key usage over time
- **Quantum Entropy Quality**: Monitor the quality of quantum entropy
- **Interactive Controls**: Test connections to KME servers and generate new quantum keys

## Accessing the Dashboard

The quantum status dashboard is available at:

```
http://localhost:8000/quantum/status
```

## Dashboard Components

### System Status

Displays the overall status of the quantum encryption system:
- **Operational**: All systems are functioning normally
- **Degraded**: Some systems are experiencing issues
- **Error**: Critical systems are not functioning

### Quantum Entropy Quality

Shows the quality of quantum entropy being generated. Higher entropy values indicate stronger randomness and security in quantum key generation.

### Encryption Statistics

Provides statistics on email encryption:
- **Total Emails**: Number of emails processed
- **Encrypted**: Number of emails encrypted with quantum encryption
- **Encryption Rate**: Percentage of emails that are quantum-encrypted

### Encryption Levels

Displays the distribution of encryption methods used:
- **Level 1: Quantum OTP** - Quantum One-Time Pad (Perfect Secrecy)
- **Level 2: Quantum-AES** - Quantum-Enhanced AES-256-GCM
- **Level 3: Post-Quantum** - Post-Quantum Cryptography (Kyber + Dilithium)
- **Level 4: Standard RSA** - Standard RSA-4096 with AES-256-GCM

### QKD Key Management Entities

Lists the quantum key distribution servers (KMEs) with their status and key availability:
- **Status**: Connected/Error
- **Keys Available**: Number of quantum keys available for encryption
- **Latency**: Connection latency in milliseconds
- **Zone**: Server location zone

### Quantum Key Usage Chart

A line chart showing quantum key usage over the past 7 days.

## Actions

The dashboard provides interactive controls to:

1. **Test KME1**: Test connection to KME Server 1
2. **Test KME2**: Test connection to KME Server 2
3. **Generate Keys**: Generate new quantum keys for encryption

## Dark Mode

The dashboard supports dark mode, which can be toggled using the theme button in the top-right corner.

## API Endpoints

The dashboard uses the following API endpoints:

- `GET /encryption/status`: Get the current encryption status
- `POST /api/v1/quantum/generate-keys`: Generate new quantum keys

For more information on API endpoints, see the [API Documentation](./api.md).

## Configuration

For information on configuring the quantum encryption system, see the [Configuration Documentation](./config.md).