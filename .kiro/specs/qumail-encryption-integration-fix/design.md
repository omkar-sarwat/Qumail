# Design Document: QuMail Encryption System Integration Fix

## Overview

This design document outlines the architecture and implementation approach for fixing the QuMail secure email encryption system. The system integrates quantum key distribution (QKD) via the Next Door Key Simulator (ETSI QKD 014 standard), Google OAuth authentication, and four levels of encryption security to provide end-to-end encrypted email communication.

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                        QuMail System                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐  │
│  │   Frontend   │◄────►│   Backend    │◄────►│   Database   │  │
│  │  (React/Vite)│      │  (FastAPI)   │      │  (SQLite)    │  │
│  └──────────────┘      └──────┬───────┘      └──────────────┘  │
│                               │                                  │
│                               ▼                                  │
│                    ┌──────────────────┐                         │
│                    │  Encryption      │                         │
│                    │  Services        │                         │
│                    │  (Level 1-4)     │                         │
│                    └────────┬─────────┘                         │
│                             │                                    │
│                             ▼                                    │
│              ┌──────────────────────────┐                       │
│              │   KM Client Manager      │                       │
│              │  (Optimized KM Client)   │                       │
│              └──────────┬───────────────┘                       │
│                         │                                        │
└─────────────────────────┼────────────────────────────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────────┐
        │  Next Door Key Simulator (ETSI QKD) │
        ├─────────────────────────────────────┤
        │  ┌──────────┐      ┌──────────┐    │
        │  │  KME1    │◄────►│  KME2    │    │
        │  │ Port 8010│      │ Port 8020│    │
        │  └──────────┘      └──────────┘    │
        └─────────────────────────────────────┘
                          │
                          ▼
                ┌──────────────────┐
                │   Gmail API      │
                │  (OAuth 2.0)     │
                └──────────────────┘
```

## Components and Interfaces

### 1. Encryption Services (Level 1-4)

#### Level 1: Quantum One-Time Pad (OTP)
**File**: `qumail-backend/app/services/encryption/level1_otp.py`

**Purpose**: Provides perfect secrecy using quantum keys from KME servers

**Key Functions**:
- `encrypt_otp(content, user_email, qkd_key, db_session, flow_id)` - Encrypts content using OTP
- `decrypt_otp(encrypted_content, user_email, metadata, db_session)` - Decrypts OTP-encrypted content

**Design Changes**:
1. Fix KME API endpoint calls to use correct ETSI QKD 014 paths
2. Ensure proper SAE ID usage (KME1: `25840139-0dd4-49ae-ba1e-b86731601803`, KME2: `c565d5aa-8670-4446-8471-b0e53e315d2a`)
3. Add comprehensive logging for key retrieval and usage
4. Store encryption metadata properly for decryption

**API Integration**:
```python
# Encryption
km1_keys = await km1_client.request_enc_keys(
    slave_sae_id="c565d5aa-8670-4446-8471-b0e53e315d2a",  # KME2's SAE ID
    number=1,
    size=required_bytes * 8
)

# Decryption
km2_keys = await km2_client.request_dec_keys(
    master_sae_id="25840139-0dd4-49ae-ba1e-b86731601803",  # KME1's SAE ID
    key_ids=[key_id]
)
```

#### Level 2: Quantum-Enhanced AES-256-GCM
**File**: `qumail-backend/app/services/encryption/level2_aes.py`

**Purpose**: Provides authenticated encryption with quantum-derived keys

**Key Functions**:
- `encrypt_aes(content, user_email)` - Encrypts using AES-256-GCM with quantum keys
- `decrypt_aes(encrypted_content, user_email, metadata)` - Decrypts AES-encrypted content

**Design Changes**:
1. Fix key derivation using HKDF with quantum material from both KME servers
2. Properly store and retrieve nonce, salt, and auth_tag in metadata
3. Fix signature verification during decryption
4. Ensure proper SAE ID usage for both encryption and decryption

#### Level 3: Post-Quantum Cryptography (PQC)
**File**: `qumail-backend/app/services/encryption/level3_pqc.py`

**Purpose**: Provides quantum-resistant encryption using Kyber1024 and Dilithium5

**Key Functions**:
- `encrypt_pqc(content, user_email)` - Encrypts using PQC algorithms
- `decrypt_pqc(encrypted_content, user_email, metadata)` - Decrypts PQC-encrypted content

**Design Changes**:
1. Ensure liboqs library is properly loaded (or use placeholder if unavailable)
2. Add optional quantum key enhancement from KME servers
3. Properly store Kyber ciphertext, Dilithium signature, and keys in metadata
4. Fix signature verification before decryption

#### Level 4: RSA-4096 + AES-256-GCM Hybrid
**File**: `qumail-backend/app/services/encryption/level4_rsa.py`

**Purpose**: Provides traditional hybrid encryption with optional quantum enhancement

**Key Functions**:
- `encrypt_rsa(content, user_email)` - Encrypts using RSA + AES hybrid
- `decrypt_rsa(encrypted_content, user_email, metadata)` - Decrypts RSA-encrypted content

**Design Changes**:
1. Store RSA private key in metadata for decryption (encrypted in production)
2. Add optional quantum key enhancement
3. Properly store encrypted session key, IV, and auth_tag
4. Fix signature verification

### 2. KM Client Manager

#### Optimized KM Client
**File**: `qumail-backend/app/services/optimized_km_client.py`

**Purpose**: Manages communication with Next Door Key Simulator KME servers

**Key Methods**:
- `request_enc_keys(slave_sae_id, number, size)` - Request encryption keys
- `request_dec_keys(master_sae_id, key_ids)` - Request decryption keys
- `check_key_status(sae_id)` - Check available keys

**Design Changes**:
1. Ensure correct ETSI QKD 014 API endpoint paths:
   - Encryption: `/api/v1/keys/{slave_sae_id}/enc_keys`
   - Decryption: `/api/v1/keys/{master_sae_id}/dec_keys`
   - Status: `/api/v1/keys/{slave_sae_id}/status`
2. Add proper error handling for HTTP errors
3. Add timeout handling (5 seconds default)
4. Support both HTTP and HTTPS modes

#### KM Client Initialization
**File**: `qumail-backend/app/services/km_client_init.py`

**Purpose**: Initializes and provides global KM client instances

**Design Changes**:
1. Read KME URLs from environment variables (default: http://127.0.0.1:8010 and http://127.0.0.1:8020)
2. Configure proper SAE IDs for each client
3. Support certificate-based authentication for HTTPS mode
4. Provide singleton pattern for client access

### 3. API Routes

#### Encryption Routes
**File**: `qumail-backend/app/api/encryption_routes.py`

**Endpoints**:
- `POST /api/v1/encryption/encrypt` - Encrypt content
- `POST /api/v1/encryption/decrypt` - Decrypt content
- `POST /api/v1/encryption/km-status` - Check KM server status
- `GET /api/v1/encryption/levels` - Get security level information

**Design Changes**:
1. Ensure all encryption levels are properly routed
2. Add proper error handling and HTTP status codes
3. Return comprehensive metadata for decryption
4. Add security audit logging

#### Email Routes
**File**: `qumail-backend/app/routes/emails.py`

**Endpoints**:
- `POST /api/v1/emails/send/quantum` - Send quantum-encrypted email
- `GET /api/v1/emails/email/{email_id}` - Get email details (encrypted)
- `POST /api/v1/emails/email/{email_id}/decrypt` - Decrypt email
- `GET /api/v1/emails/{folder}` - Get emails from folder

**Design Changes**:
1. Fix quantum email sending to properly encrypt before Gmail API call
2. Ensure email details endpoint returns encrypted content without auto-decryption
3. Add proper access control for decryption endpoint
4. Store encryption metadata in database for later decryption

### 4. Google OAuth Integration

#### OAuth Service
**File**: `qumail-backend/app/services/gmail_oauth.py`

**Purpose**: Manages Google OAuth 2.0 authentication flow

**Key Methods**:
- `get_authorization_url()` - Generate OAuth consent URL
- `exchange_code_for_tokens(code)` - Exchange authorization code for tokens
- `refresh_access_token(user_email, db)` - Refresh expired tokens
- `revoke_tokens(user_email, db)` - Revoke user tokens

**Design Changes**:
1. Ensure proper OAuth scopes for Gmail API access
2. Store tokens encrypted in database
3. Implement automatic token refresh
4. Add proper error handling for OAuth failures

#### Gmail Service
**File**: `qumail-backend/app/services/gmail_service.py`

**Purpose**: Interacts with Gmail API for email operations

**Key Methods**:
- `send_email(access_token, message)` - Send email via Gmail API
- `fetch_emails(access_token, folder, max_results, page_token)` - Fetch emails
- `get_email_by_id(access_token, email_id)` - Get email details
- `mark_as_read(access_token, email_id)` - Mark email as read

**Design Changes**:
1. Ensure proper MIME message creation for encrypted content
2. Add support for sending base64-encoded ciphertext
3. Implement proper error handling for Gmail API errors
4. Add retry logic for transient failures

### 5. Database Schema

#### Email Model
**File**: `qumail-backend/app/models/email.py`

**Fields**:
- `id` (UUID) - Primary key
- `flow_id` (String) - Unique flow identifier
- `sender_email` (String) - Sender email address
- `receiver_email` (String) - Receiver email address
- `user_id` (UUID) - Foreign key to users table
- `subject` (Text) - Email subject
- `body_encrypted` (Text) - Base64-encoded encrypted body
- `encryption_key_id` (String) - Key ID from quantum pool
- `encryption_algorithm` (String) - Algorithm used
- `encryption_iv` (Text) - Initialization vector
- `encryption_auth_tag` (Text) - Authentication tag
- `encryption_metadata` (JSON) - Additional metadata
- `security_level` (Integer) - Security level (1-4)
- `direction` (Enum) - SENT or RECEIVED
- `timestamp` (DateTime) - Email timestamp
- `is_read` (Boolean) - Read status
- `gmail_message_id` (String) - Gmail message ID

**Design Changes**:
1. Ensure proper foreign key relationships with users table
2. Add indexes on frequently queried fields (flow_id, security_level, direction)
3. Store all encryption metadata required for decryption
4. Support both UUID and integer ID formats for compatibility

## Data Models

### Encryption Request
```python
{
    "content": str,
    "user_email": str,
    "security_level": int (1-4)
}
```

### Encryption Response
```python
{
    "encrypted_content": str (base64),
    "security_level": int,
    "encryption_algorithm": str,
    "signature": str (base64),
    "metadata": {
        "flow_id": str,
        "key_id": str,
        "algorithm": str,
        "nonce": str (base64),
        "salt": str (base64),
        "auth_tag": str (base64),
        ...
    },
    "success": bool
}
```

### Decryption Request
```python
{
    "encrypted_content": str (base64),
    "user_email": str,
    "security_level": int (1-4),
    "metadata": dict
}
```

### Decryption Response
```python
{
    "decrypted_content": str,
    "security_level": int,
    "signature_valid": bool,
    "tampering_detected": bool,
    "success": bool,
    "message": str
}
```

## Error Handling

### Error Types
1. **Level1SecurityError** - OTP encryption/decryption errors
2. **Level2SecurityError** - AES encryption/decryption errors
3. **Level3SecurityError** - PQC encryption/decryption errors
4. **Level4SecurityError** - RSA encryption/decryption errors
5. **InsufficientKeysError** - Not enough quantum keys available
6. **KMError** - KME server communication errors
7. **SecurityError** - General security violations

### Error Response Format
```python
{
    "detail": str,
    "status_code": int,
    "error_type": str,
    "timestamp": str (ISO 8601)
}
```

## Testing Strategy

### Unit Tests
1. Test each encryption level independently
2. Test KM client API calls with mocked responses
3. Test OAuth flow with mocked Google API
4. Test database operations with test database

### Integration Tests
1. Test end-to-end encryption flow (encrypt → store → retrieve → decrypt)
2. Test KME server integration with Next Door Key Simulator
3. Test Gmail API integration with test account
4. Test all four security levels with real quantum keys

### System Tests
1. Start all services (KME1, KME2, backend, frontend)
2. Test complete email flow from compose to decrypt
3. Verify encrypted content in Gmail
4. Verify decryption in QuMail
5. Test error scenarios (KME offline, invalid keys, etc.)

## Security Considerations

### Key Management
1. Quantum keys are one-time use only (OTP principle)
2. Keys are never stored in plaintext in database
3. Key IDs are tracked to prevent reuse
4. Keys are automatically consumed after decryption

### Access Control
1. Only sender and receiver can decrypt emails
2. User authentication required for all operations
3. OAuth tokens stored encrypted in database
4. Session tokens expire after inactivity

### Data Protection
1. Email bodies stored encrypted in database
2. Encryption metadata stored separately
3. No plaintext content in Gmail
4. Comprehensive audit logging for security events

### Network Security
1. Support for TLS/SSL with certificate authentication
2. Timeout handling for network requests
3. Retry logic for transient failures
4. Rate limiting on API endpoints

## Deployment Configuration

### Environment Variables
```bash
# Backend
KM1_BASE_URL=http://127.0.0.1:8010
KM2_BASE_URL=http://127.0.0.1:8020
DATABASE_URL=sqlite:///./qumail.db
SECRET_KEY=<generated-secret-key>
GOOGLE_CLIENT_ID=<google-oauth-client-id>
GOOGLE_CLIENT_SECRET=<google-oauth-client-secret>
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback

# Next Door Key Simulator (KME1)
KME_ID=1
PORT=8010
MAX_KEY_COUNT=1000
KEY_GEN_BATCH_SIZE=100
REFILL_THRESHOLD=500
OTHER_KMES=http://127.0.0.1:8020

# Next Door Key Simulator (KME2)
KME_ID=2
PORT=8020
MAX_KEY_COUNT=1000
OTHER_KMES=http://127.0.0.1:8010
```

### Service Startup Order
1. Start KME1 (Next Door Key Simulator)
2. Start KME2 (Next Door Key Simulator)
3. Wait 5 seconds for KME synchronization
4. Start Backend (FastAPI)
5. Start Frontend (Vite dev server)

### Health Checks
1. Backend health endpoint: `GET /health`
2. KME1 status: `GET http://localhost:8010/api/v1/kme/status`
3. KME2 status: `GET http://localhost:8020/api/v1/kme/status`
4. Encryption status: `GET /encryption/status`

## Performance Considerations

### Optimization Strategies
1. Use connection pooling for KME API calls
2. Cache KM client instances globally
3. Implement async/await for all I/O operations
4. Use database indexes for frequently queried fields
5. Implement pagination for email lists

### Expected Performance
- Encryption time: 50-200ms per email (depending on security level)
- Decryption time: 40-150ms per email
- KME API latency: 10-50ms per request
- Gmail API latency: 100-500ms per request

## Monitoring and Logging

### Log Levels
- **DEBUG**: Key material previews (first 16 bytes only), detailed flow
- **INFO**: Encryption/decryption operations, API calls, user actions
- **WARNING**: Degraded performance, low key availability, token refresh
- **ERROR**: Encryption failures, API errors, database errors
- **CRITICAL**: Security violations, tampering detected, system failures

### Metrics to Track
1. Encryption operations per security level
2. KME server availability and latency
3. Quantum key usage and availability
4. OAuth token refresh rate
5. API error rates
6. Email send/receive success rates

## Migration Path

### Phase 1: Fix Core Encryption (Priority: Critical)
1. Fix KM client API endpoints
2. Fix encryption service implementations
3. Fix metadata storage and retrieval
4. Add comprehensive logging

### Phase 2: Fix API Routes (Priority: High)
1. Fix encryption API routes
2. Fix email API routes
3. Add proper error handling
4. Add security audit logging

### Phase 3: Integrate OAuth (Priority: High)
1. Fix OAuth flow
2. Fix token storage and refresh
3. Integrate with Gmail API
4. Test end-to-end flow

### Phase 4: Testing and Validation (Priority: Medium)
1. Create comprehensive test suite
2. Test all security levels
3. Test error scenarios
4. Performance testing

### Phase 5: Documentation and Deployment (Priority: Low)
1. Update API documentation
2. Create deployment guide
3. Create user guide
4. Production deployment
