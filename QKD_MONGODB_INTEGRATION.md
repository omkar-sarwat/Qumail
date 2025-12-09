# QKD MongoDB Integration - Complete Documentation

## Overview

All Quantum Key Distribution (QKD) data in QuMail is now stored in MongoDB for complete lifecycle tracking, auditing, and analysis. This includes quantum keys, sessions, and audit logs.

## MongoDB Collections

### 1. `qkd_keys` Collection

Stores all quantum keys retrieved from KME servers.

**Document Structure:**
```javascript
{
  "_id": "uuid",
  "key_id": "uuid",                    // Primary key identifier
  "kme1_key_id": "uuid",               // Key ID from KME1 (sender's KME)
  "kme2_key_id": "uuid",               // Key ID from KME2 (receiver's KME)
  "key_material_encrypted": "base64",  // Encrypted key material (optional)
  "key_hash": "sha256-hash",           // Hash for integrity verification
  "key_size_bits": 256,                // Key size in bits
  "source_kme": "KME1",                // Which KME the key came from
  "sae1_id": "uuid",                   // Sender's SAE ID
  "sae2_id": "uuid",                   // Receiver's SAE ID
  "sender_email": "sender@example.com",
  "receiver_email": "receiver@example.com",
  "flow_id": "uuid",                   // Associated email flow ID
  "email_id": "uuid",                  // Associated email ID
  "security_level": 1,                 // 1=OTP, 2=AES, 3=PQC, 4=RSA
  "algorithm": "OTP-QKD-ETSI-014",
  "state": "consumed",                 // ready, reserved, consumed, expired, revoked
  "is_consumed": true,
  "consumed_by": "user_id",
  "consumed_at": "2025-12-09T10:00:00Z",
  "created_at": "2025-12-09T10:00:00Z",
  "expires_at": "2025-12-10T10:00:00Z",
  "entropy_score": 1.0,
  "quality_score": 1.0,
  "quantum_grade": true,
  "operation_history": [
    {
      "operation": "USED_FOR_EMAIL_ENCRYPTION",
      "timestamp": "2025-12-09T10:00:00Z",
      "flow_id": "uuid"
    }
  ]
}
```

### 2. `qkd_sessions` Collection

Tracks QKD sessions between sender and receiver.

**Document Structure:**
```javascript
{
  "_id": "uuid",
  "session_id": "uuid",
  "flow_id": "uuid",
  "sender_email": "sender@example.com",
  "sender_sae_id": "uuid",
  "receiver_email": "receiver@example.com",
  "receiver_sae_id": "uuid",
  "kme1_endpoint": "https://kme1.example.com",
  "kme2_endpoint": "https://kme2.example.com",
  "key_ids": ["key1", "key2"],
  "total_keys_used": 2,
  "total_bits_exchanged": 512,
  "is_active": false,
  "is_successful": true,
  "error_message": null,
  "security_level": 1,
  "encryption_algorithm": "OTP-QKD-ETSI-014",
  "started_at": "2025-12-09T10:00:00Z",
  "completed_at": "2025-12-09T10:01:00Z",
  "expires_at": "2025-12-10T10:00:00Z"
}
```

### 3. `qkd_audit_logs` Collection

Records all QKD operations for security auditing.

**Document Structure:**
```javascript
{
  "_id": "uuid",
  "operation": "EMAIL_ENCRYPTED",      // Operation type
  "key_id": "uuid",
  "session_id": "uuid",
  "flow_id": "uuid",
  "user_email": "user@example.com",
  "user_id": "uuid",
  "ip_address": "192.168.1.1",
  "user_agent": "QuMail/1.0",
  "success": true,
  "error_message": null,
  "details": {
    "security_level": 1,
    "algorithm": "OTP-QKD-ETSI-014"
  },
  "timestamp": "2025-12-09T10:00:00Z",
  "severity": "INFO"
}
```

**Operation Types:**
- `KEY_GENERATED` - New key retrieved from KME
- `KEY_ACCESSED` - Key accessed for use
- `KEY_CONSUMED` - Key marked as used (one-time)
- `KEY_EXPIRED` - Key expired
- `SESSION_CREATED` - New QKD session started
- `SESSION_COMPLETED` - Session completed
- `EMAIL_ENCRYPTED` - Email encrypted with QKD key
- `EMAIL_DECRYPTED` - Email decrypted with QKD key
- `EXPIRED_KEYS_CLEANUP` - Cleanup operation

### 4. `qkd_pool_status` Collection

Monitors the status of QKD key pools.

**Document Structure:**
```javascript
{
  "_id": "uuid",
  "kme_id": "KME1",
  "sae_id": "uuid",
  "total_keys": 100,
  "available_keys": 75,
  "reserved_keys": 5,
  "consumed_keys": 20,
  "expired_keys": 0,
  "pool_capacity": 1000,
  "utilization_percent": 10.0,
  "last_key_generated": "2025-12-09T10:00:00Z",
  "last_key_consumed": "2025-12-09T09:55:00Z",
  "is_healthy": true,
  "last_health_check": "2025-12-09T10:00:00Z",
  "error_count": 0,
  "created_at": "2025-12-08T00:00:00Z",
  "updated_at": "2025-12-09T10:00:00Z"
}
```

## API Endpoints

### QKD Statistics

```http
GET /api/v1/qkd/statistics
Authorization: Bearer <token>

Response:
{
  "success": true,
  "keys": {
    "ready": 50,
    "reserved": 5,
    "consumed": 100,
    "expired": 10,
    "total": 165
  },
  "sessions": {
    "total_sessions": 50,
    "active_sessions": 2,
    "successful_sessions": 48,
    "total_keys_used": 100,
    "total_bits_exchanged": 25600
  },
  "timestamp": "2025-12-09T10:00:00Z"
}
```

### List QKD Keys

```http
GET /api/v1/qkd/keys?limit=50&include_consumed=false&security_level=1
Authorization: Bearer <token>

Response:
{
  "success": true,
  "count": 10,
  "keys": [
    {
      "_id": "uuid",
      "key_id": "uuid",
      "key_material_encrypted": "[REDACTED]",
      ...
    }
  ]
}
```

### Get Key Details

```http
GET /api/v1/qkd/keys/{key_id}
Authorization: Bearer <token>

Response:
{
  "success": true,
  "key": {...},
  "audit_logs": [...]
}
```

### Get Keys by Flow ID

```http
GET /api/v1/qkd/keys/flow/{flow_id}
Authorization: Bearer <token>

Response:
{
  "success": true,
  "flow_id": "uuid",
  "count": 3,
  "keys": [...]
}
```

### List QKD Sessions

```http
GET /api/v1/qkd/sessions?limit=50&active_only=false
Authorization: Bearer <token>

Response:
{
  "success": true,
  "count": 10,
  "sessions": [...]
}
```

### Get Session Details

```http
GET /api/v1/qkd/sessions/{session_id}
Authorization: Bearer <token>

Response:
{
  "success": true,
  "session": {...},
  "keys": [...],
  "audit_logs": [...]
}
```

### List Audit Logs

```http
GET /api/v1/qkd/audit-logs?hours=24&limit=100&operation=EMAIL_ENCRYPTED&errors_only=false
Authorization: Bearer <token>

Response:
{
  "success": true,
  "count": 50,
  "logs": [...]
}
```

### Get Pool Status

```http
GET /api/v1/qkd/pool-status
Authorization: Bearer <token>

Response:
{
  "success": true,
  "pools": [
    {
      "kme_id": "KME1",
      "available_keys": 75,
      ...
    }
  ],
  "timestamp": "2025-12-09T10:00:00Z"
}
```

### Cleanup Expired Keys

```http
POST /api/v1/qkd/cleanup-expired
Authorization: Bearer <token>

Response:
{
  "success": true,
  "expired_keys_cleaned": 5,
  "timestamp": "2025-12-09T10:00:00Z"
}
```

## Data Flow

### Email Encryption

1. User sends encrypted email
2. `complete_email_service.send_encrypted_email()` is called
3. `_encrypt_by_level()` retrieves quantum keys from KME
4. QKD Session is created in MongoDB (`qkd_sessions`)
5. QKD Keys are stored in MongoDB (`qkd_keys`)
6. Audit log entry created (`qkd_audit_logs`)
7. Email is stored with encryption metadata

### Email Decryption

1. User opens encrypted email
2. `receive_and_decrypt_email()` is called
3. Keys are retrieved from local cache or KME
4. Decryption is performed
5. Audit log entry created (`qkd_audit_logs`)
6. Decrypted content is cached

## Files Modified/Created

### New Files

- `app/mongo_models.py` - Added QKD document models:
  - `QKDKeyState` (Enum)
  - `QKDKeyDocument`
  - `QKDSessionDocument`
  - `QKDAuditLogDocument`
  - `QKDKeyPoolStatusDocument`

- `app/mongo_repositories.py` - Added QKD repositories:
  - `QKDKeyRepository`
  - `QKDSessionRepository`
  - `QKDAuditLogRepository`
  - `QKDKeyPoolStatusRepository`

- `app/services/qkd_mongo_service.py` - QKD MongoDB integration service

- `app/routes/qkd.py` - QKD API routes

### Modified Files

- `app/services/complete_email_service.py` - Added QKD MongoDB storage on encrypt/decrypt
- `app/main.py` - Registered QKD routes

## Security Considerations

1. **Key Material**: Actual key material is stored encrypted and redacted in API responses
2. **Access Control**: Users can only view their own keys and sessions
3. **Audit Trail**: All operations are logged for compliance
4. **Key Expiration**: Keys are automatically marked as expired after 24 hours
5. **One-Time Use**: Consumed keys cannot be reused

## Querying MongoDB Directly

You can query the QKD collections directly in MongoDB:

```javascript
// Find all keys for a user
db.qkd_keys.find({ sender_email: "user@example.com" })

// Find all consumed keys
db.qkd_keys.find({ state: "consumed" })

// Find sessions in the last 24 hours
db.qkd_sessions.find({ 
  started_at: { $gte: new Date(Date.now() - 24*60*60*1000) }
})

// Get audit logs for errors
db.qkd_audit_logs.find({ success: false })

// Get key statistics
db.qkd_keys.aggregate([
  { $group: { _id: "$state", count: { $sum: 1 } } }
])
```

## Environment Variables

No new environment variables are required. The QKD collections use the same MongoDB connection as other collections.

## Migration Notes

- Existing emails will not have QKD records
- New emails sent after this update will have full QKD tracking
- Run cleanup endpoint periodically to remove expired keys
