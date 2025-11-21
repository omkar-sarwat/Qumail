# QuMail Secure Email Backend

A quantum-enhanced secure email system with multiple encryption levels, built using FastAPI and integrated with ETSI GS QKD-014 compliant Key Management (KM) servers.

## 🔐 Security Levels

QuMail provides four distinct security levels for email encryption:

### Level 1: Quantum One-Time Pad (Perfect Secrecy)
- **Algorithm**: One-Time Pad with quantum key combination
- **Key Source**: Quantum keys from both KME1 and KME2
- **Signature**: RSA-PSS with SHA-256
- **Security Rating**: Maximum (Information-theoretic security)
- **Use Case**: Ultra-sensitive communications requiring perfect secrecy

### Level 2: Quantum-Enhanced AES (Very High Security)
- **Algorithm**: AES-256-GCM with HKDF key derivation
- **Key Source**: Quantum keys from both KM servers
- **Signature**: RSA-PSS with SHA-256
- **Security Rating**: Very High
- **Use Case**: High-security business communications

### Level 3: Post-Quantum Cryptography (Future-Proof)
- **Algorithm**: Kyber1024 + Dilithium5 + AES-256-GCM
- **Key Source**: Kyber KEM with quantum key enhancement
- **Signature**: Dilithium5 post-quantum signatures
- **Security Rating**: Future-Proof High
- **Use Case**: Future-proof communications against quantum computers

### Level 4: Standard RSA (Compatibility)
- **Algorithm**: RSA-4096-OAEP + AES-256-GCM
- **Key Source**: RSA key pairs with HKDF session keys
- **Signature**: RSA-PSS with SHA-256
- **Security Rating**: Standard High
- **Use Case**: General secure communications and fallback option

## 🛡️ Key Features

- **ETSI GS QKD-014 Compliance**: Full integration with quantum key distribution standards
- **Multi-Level Encryption**: Four distinct security levels for different use cases
- **Gmail API Integration**: Seamless OAuth 2.0 integration with Gmail
- **Quantum Key Management**: Real-time quantum key consumption from dual KM servers
- **Digital Signatures**: All encryption levels include digital signature verification
- **Tampering Detection**: Comprehensive security incident logging and monitoring
- **Certificate-Based Authentication**: Mutual TLS authentication with KM servers
- **Security Audit Logging**: Complete audit trail of all security events
- **Rate Limiting**: Protection against API abuse
- **Comprehensive Error Handling**: Security-focused error responses

## 📋 Prerequisites

### System Requirements
- Python 3.11+
- PostgreSQL 12+ (recommended) or SQLite (development)
- OpenSSL 1.1.1+
- Git

### External Dependencies
- **qkd_kme_server-master**: ETSI-compliant KM servers running on ports 13000 and 14000
- **Google OAuth 2.0**: Client credentials for Gmail API access
- **Valid Certificates**: Client certificates for KM server authentication

## 🚀 Quick Start

### 1. Prerequisites Setup

Ensure you have the following installed:
- **Python 3.11+** - Required for modern async features
- **Git** - For version control
- **OpenSSL** - For certificate operations

### 2. Clone and Initial Setup

```bash
# Clone the repository
git clone <repository-url>
cd qumail-secure-email/qumail-backend

# Copy environment template
cp .env.example .env  # Linux/macOS
copy .env.example .env  # Windows
```

### 3. Environment Configuration

Edit `.env` file with your specific configuration:

```bash
# Generate a secure secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate a Fernet encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Configure Google OAuth (required for Gmail integration)
# 1. Go to https://console.cloud.google.com/
# 2. Create a new project or select existing
# 3. Enable Gmail API
# 4. Create OAuth 2.0 credentials
# 5. Add redirect URI: http://localhost:3000/auth/callback
```

### 4. Start Development Environment

#### Option A: Automated Setup (Windows)
```powershell
# PowerShell script (recommended for Windows)
.\start.ps1

# Or batch file
start.bat
```

#### Option B: Manual Setup (All platforms)
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Validate configuration
python validate_backend.py

# Initialize database
alembic upgrade head

# Start the development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Verify Installation

```bash
# Check API documentation
open http://localhost:8000/docs

# Test health endpoint
curl http://localhost:8000/health

# Validate backend configuration
python validate_backend.py
```

## ⚙️ Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure the following:

#### Application Settings
```bash
APP_NAME=QuMail Secure Email Backend
APP_VERSION=1.0.0-secure
APP_ENV=development  # or production
DEBUG=true  # Set to false in production
```

#### Security Configuration
```bash
# Generate a secure secret key (minimum 32 characters)
SECRET_KEY=your-super-secret-key-here-change-this-in-production

# Generate a Fernet encryption key
ENCRYPTION_MASTER_KEY=your-fernet-encryption-key-here-base64-encoded
```

To generate a Fernet key:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

#### Database Configuration
```bash
# PostgreSQL (recommended for production)
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/qumail

# SQLite (development only)
DATABASE_URL=sqlite+aiosqlite:///./qumail.db
```

#### Google OAuth Configuration
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Gmail API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URIs

```bash
GOOGLE_CLIENT_ID=your-google-oauth-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-oauth-client-secret
GOOGLE_REDIRECT_URI=http://localhost:3000/auth/callback
```

#### KM Server Configuration
```bash
# KM server URLs (from qkd_kme_server-master)
KM1_BASE_URL=https://localhost:13000
KM2_BASE_URL=https://localhost:14000

# Client certificates for SAE authentication
KM1_CLIENT_CERT_PFX=../qkd_kme_server-master/certs/kme-1-local-zone/client_1.pfx
KM2_CLIENT_CERT_PFX=../qkd_kme_server-master/certs/kme-2-local-zone/client_3.pfx

# CA certificates for server verification
KM1_CA_CERT=../qkd_kme_server-master/certs/kme-1-local-zone/ca.crt
KM2_CA_CERT=../qkd_kme_server-master/certs/kme-2-local-zone/ca.crt

# SAE IDs from certificate analysis
SENDER_SAE_ID=1
RECEIVER_SAE_ID=3
```

## 🗄️ Database Setup

### SQLite (Development)
```bash
# SQLite is included with Python, no additional setup required
# Default configuration in .env:
DATABASE_URL=sqlite+aiosqlite:///./qumail.db
```

### PostgreSQL (Production)
```bash
# Install PostgreSQL
# Windows: Download from postgresql.org
# Ubuntu/Debian: sudo apt-get install postgresql postgresql-contrib
# macOS: brew install postgresql

# Create database and user
sudo -u postgres psql  # Linux/macOS
# Or use pgAdmin on Windows
CREATE DATABASE qumail;
CREATE USER qumail_user WITH ENCRYPTED PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE qumail TO qumail_user;
\q

# Update DATABASE_URL in .env
DATABASE_URL=postgresql+asyncpg://qumail_user:secure_password@localhost:5432/qumail
```

## 🔑 Certificate Setup

Ensure the qkd_kme_server-master is properly configured and certificates are available:

```bash
# Verify certificate files exist
ls -la ../qkd_kme_server-master/certs/kme-1-local-zone/
ls -la ../qkd_kme_server-master/certs/kme-2-local-zone/

# Required files:
# - client_1.pfx (KM1 client certificate)
# - client_3.pfx (KM2 client certificate)
# - ca.crt (CA certificates for both zones)
```

## 🏃‍♂️ Running the Application

### Development Mode
```bash
# Using the startup scripts (Windows)
.\start.ps1  # PowerShell
start.bat    # Batch file

# Or manually (all platforms)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode
```bash
# Set environment to production in .env
APP_ENV=production
DEBUG=false

# Install production server
pip install gunicorn

# Start with Gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 📚 API Documentation

When running in development mode, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

#### Authentication
- `GET /api/v1/auth/google` - Get OAuth authorization URL
- `GET /api/v1/auth/google/callback` - Handle OAuth callback
- `POST /api/v1/auth/revoke` - Revoke user tokens
- `GET /api/v1/auth/validate` - Validate session token

#### Email Operations
- `POST /api/v1/messages` - Get Gmail messages
- `GET /api/v1/messages/{message_id}` - Get message details
- `POST /api/v1/messages/send` - Send secure email
- `POST /api/v1/messages/{message_id}/modify` - Modify message labels
- `GET /api/v1/labels` - Get Gmail labels

#### Encryption Services
- `POST /api/v1/encryption/encrypt` - Encrypt content
- `POST /api/v1/encryption/decrypt` - Decrypt content
- `POST /api/v1/encryption/km-status` - Check KM server status
- `GET /api/v1/encryption/levels` - Get security level information

#### System Status
- `GET /health` - Health check
- `GET /status` - System status
- `GET /metrics` - System metrics

## 🧪 Testing

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-httpx

# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_encryption.py

# Run specific test
pytest tests/test_encryption.py::test_level1_encryption
```

### Manual Testing

#### Test KM Server Connectivity
```bash
# Check if KM servers are reachable
curl -k https://localhost:13000/api/v1/keys/status
curl -k https://localhost:14000/api/v1/keys/status
```

#### Test OAuth Flow
1. Visit: http://localhost:8000/api/v1/auth/google
2. Complete Google authorization
3. Verify callback success

#### Test Encryption
```bash
# Test encryption endpoint
curl -X POST "http://localhost:8000/api/v1/encryption/encrypt" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Test message",
    "security_level": "LEVEL_1",
    "user_email": "test@example.com"
  }'
```

## 🛡️ Security Considerations

### Production Security Checklist

- [ ] Change all default passwords and keys
- [ ] Use PostgreSQL instead of SQLite
- [ ] Enable HTTPS with valid certificates
- [ ] Set `DEBUG=false`
- [ ] Configure proper CORS origins
- [ ] Enable rate limiting
- [ ] Set up monitoring and alerting
- [ ] Regular security updates
- [ ] Backup strategy implementation
- [ ] Network security (firewall, VPN)

### Certificate Management
- Regularly rotate client certificates
- Monitor certificate expiration dates
- Secure certificate storage
- Implement certificate revocation procedures

### Key Management
- Regular quantum key consumption monitoring
- KM server health monitoring
- Backup key management procedures
- Key rotation policies

## 🔍 Monitoring and Logging

### Log Files
- Application logs: `qumail-backend.log`
- Access logs: `logs/access.log` (production)
- Error logs: `logs/error.log` (production)

### Health Checks
- Application health: `GET /health`
- System status: `GET /status`
- KM server status: `POST /api/v1/encryption/km-status`

### Security Monitoring
- All security events are logged to the security audit system
- Failed authentication attempts are tracked
- Encryption/decryption operations are audited
- Tampering attempts are detected and logged

## 🐛 Troubleshooting

### Common Issues

#### KM Server Connection Errors
```
Error: KM server not reachable
```
**Solution**: 
1. Ensure qkd_kme_server-master is running
2. Check certificate paths in .env
3. Verify KM server URLs (ports 13000, 14000)

#### Database Connection Errors
```
Error: could not connect to server
```
**Solution**:
1. Ensure PostgreSQL is running
2. Check DATABASE_URL format
3. Verify database credentials

#### OAuth Configuration Errors
```
Error: invalid_client
```
**Solution**:
1. Verify Google OAuth credentials
2. Check redirect URI configuration
3. Ensure Gmail API is enabled

#### Certificate Errors
```
Error: certificate verify failed
```
**Solution**:
1. Check certificate file paths
2. Verify certificate validity
3. Ensure CA certificates are correct

### Debug Mode
Enable debug logging by setting:
```bash
LOG_LEVEL=DEBUG
DEBUG=true
```

### Getting Help
1. Check the logs: `tail -f qumail-backend.log`
2. Verify configuration: ensure all required environment variables are set
3. Test individual components: use the debug endpoints in development mode
4. Check KM server logs for authentication issues

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

### Code Style
- Follow PEP 8 style guidelines
- Use Black for code formatting
- Add type hints for all functions
- Include docstrings for public methods
- Write comprehensive tests

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- ETSI GS QKD-014 standard for quantum key distribution
- qkd_kme_server-master for ETSI-compliant KM implementation
- FastAPI framework for robust API development
- Google Gmail API for email integration
- Cryptography library for security implementations

## 📞 Support

For support, please check:
1. This README for common solutions
2. Application logs for error details
3. API documentation at `/docs`
4. GitHub issues for known problems

---

**⚠️ Security Notice**: This system handles sensitive cryptographic operations. Always follow security best practices, keep dependencies updated, and regularly audit your configuration in production environments.