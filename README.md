# QuMail Secure Email with Quantum Key Distribution

This project implements a secure email system featuring quantum key distribution (QKD) for enhanced security. The system follows the ETSI QKD standard and includes three main components:

1. **QKD Key Management Entity (KME) Servers** - Based on the ETSI standard
2. **Backend API** - FastAPI server that handles email processing and quantum key integration
3. **Frontend Client** - React application that provides the user interface

## System Architecture

The system consists of the following components working together:

- **KME Servers**: Two KME servers (Alice and Bob) communicate with each other to establish quantum keys
- **Backend Server**: Integrates with the KME servers to provide quantum-secured email functionality
- **Frontend Client**: React application that allows users to send and receive quantum-secured emails

## Requirements

- Rust (for KME servers)
- Python 3.8+ (for backend)
- Node.js 16+ (for frontend)
- PowerShell (for startup scripts)

## Getting Started

### Option 1: Start All Components Together

To start the entire system (KME servers, backend, and frontend) with a single command:

```powershell
.\start_all.ps1
```

This script will:
1. Start both KME servers
2. Start the backend API server
3. Start the frontend development server
4. Open the application in your default web browser

### Option 2: Start Components Separately

If you prefer to start each component separately:

1. Start the KME servers:
```powershell
.\start_kme_servers.ps1
```

2. Start the backend and frontend:
```powershell
.\start_qumail.ps1
```

## System URLs

After starting the system, the following services will be available:

- **Frontend**: [http://localhost:3000](http://localhost:3000)
- **Backend API**: [http://localhost:8001](http://localhost:8001)
- **KME1 Debug Interface**: [http://localhost:18080](http://localhost:18080)
- **KME1 API**: https://localhost:13000
- **KME2 API**: https://localhost:14000

## Usage Instructions

1. Open the frontend URL ([http://localhost:3000](http://localhost:3000))
2. Log in with your credentials
3. Navigate to the Quantum Dashboard to view and manage quantum keys
4. When composing emails, the system will automatically check for available quantum keys for encryption
5. The system supports multiple encryption methods based on quantum key availability:
   - One-Time Pad (highest security, requires quantum keys)
   - Quantum-aided AES (high security, uses quantum randomness)
   - Post-quantum cryptography (fallback if quantum keys are unavailable)

## Testing the System

We've added several test scripts to help you verify the system is working correctly:

### Running Tests

1. **Run all tests** - Tests KME connections and all encryption levels:
   ```
   # Windows
   run_tests.bat
   
   # Linux/macOS
   ./run_tests.sh
   ```

2. **Test KME server connections**:
   ```
   python test_km_connections.py
   ```

3. **Test all encryption levels**:
   ```
   cd qumail-backend
   python test_all_encryption.py
   ```

4. **Test only post-quantum encryption**:
   ```
   cd qumail-backend
   python test_pqc.py
   ```

### Security Levels

The system implements four levels of security:

1. **Level 1 (OTP)**: Quantum One-Time Pad - unconditionally secure with quantum keys
2. **Level 2 (AES-256-GCM)**: AES with quantum-enhanced key derivation
3. **Level 3 (PQC)**: Post-Quantum Cryptography using Kyber1024 and Dilithium5
4. **Level 4 (RSA+AES)**: Hybrid RSA+AES for legacy compatibility

## Troubleshooting

If you encounter issues:

1. Check that all required ports are available (3000, 8001, 13000, 14000, 18080)
2. Ensure all dependencies are installed (Rust, Python, Node.js, liboqs optional)
3. Check the KME debug interface for quantum key status
4. If the KME servers fail to start, check that the raw key files are present in the specified directories
5. For Post-Quantum Cryptography, the system can work with or without the liboqs library

## Components in Detail

### QKD KME Server

The KME server implements the ETSI QKD standard, managing quantum keys between secure application entities (SAEs). It:
- Monitors directories for new quantum key files
- Establishes secure connections between KMEs
- Provides APIs for key status and retrieval
- Authenticates SAEs using SSL certificates

### Backend API

The backend provides:
- Email processing and storage
- Integration with the KME servers for quantum key retrieval
- Multiple encryption methods depending on key availability
- User authentication and management

### Frontend Client

The frontend provides:
- User authentication
- Email composition and viewing
- Quantum dashboard for key management
- Visual indicators of encryption status

## Quantum Security Features

The system implements multiple layers of quantum security:

1. **Quantum Key Distribution (QKD)**: Uses quantum physics to generate and distribute secure keys
2. **One-Time Pad Encryption**: When available, uses QKD keys for theoretically unbreakable encryption
3. **Quantum-Aided AES**: Uses quantum randomness to strengthen AES encryption
4. **Post-Quantum Cryptography**: Implements algorithms resistant to quantum computer attacks

## Contributing

Contributions to any component of the system are welcome. Please ensure you understand the ETSI QKD standard before making changes to the KME server components.

## License

This project is licensed under the terms provided in the LICENSE file of each component.