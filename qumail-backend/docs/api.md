# QuMail Secure Email API Documentation

This document provides an overview of the QuMail Secure Email API endpoints.

## Base URL

```
http://localhost:8000
```

## Authentication

Most endpoints require authentication via OAuth 2.0 with Google.

```
Authorization: Bearer <access_token>
```

## API Endpoints

### Authentication

#### OAuth 2.0 Google Login

```
GET /api/v1/auth/google
```

Redirects to Google OAuth 2.0 authentication flow.

#### OAuth 2.0 Google Callback

```
GET /api/v1/auth/google/callback
```

Callback endpoint for Google OAuth 2.0 flow.

#### Get Current User

```
GET /api/v1/auth/me
```

Returns information about the currently authenticated user.

### Emails

#### Get Emails

```
GET /emails?folder={folder}&maxResults={maxResults}
```

Get emails from specified folder.

**Query Parameters:**
- `folder` - Email folder (inbox, sent)
- `maxResults` - Maximum number of emails to return

**Response:**
```json
{
  "emails": [
    {
      "id": "string",
      "flow_id": "string",
      "sender": "string",
      "receiver": "string",
      "subject": "string",
      "timestamp": "string",
      "isRead": true,
      "isStarred": false,
      "securityLevel": 2,
      "direction": "received",
      "isSuspicious": false
    }
  ],
  "totalCount": 0,
  "nextPageToken": "string",
  "userEmail": "string"
}
```

#### Send Email

```
POST /emails/send
```

Send an email with quantum encryption.

**Request Body:**
```json
{
  "subject": "string",
  "body": "string",
  "recipient": "string",
  "securityLevel": 2
}
```

**Response:**
```json
{
  "success": true,
  "emailId": "string",
  "flowId": "string",
  "encryptionMethod": "string",
  "securityLevel": 2,
  "entropy": 0.99,
  "keyId": "string",
  "encryptedSize": 0,
  "timestamp": "string",
  "message": "string"
}
```

### Quantum Status

#### Quantum Status Dashboard

```
GET /quantum/status
```

Returns the quantum status dashboard HTML page.

#### Encryption Status

```
GET /encryption/status
```

Get encryption status with simulated quantum keys.

**Response:**
```json
{
  "kmeStatus": [
    {
      "id": "string",
      "name": "string",
      "status": "string",
      "latency": 0,
      "keysAvailable": 0,
      "maxKeySize": 0,
      "averageEntropy": 0.0,
      "keyGenRate": 0,
      "zone": "string"
    }
  ],
  "quantumKeysAvailable": 0,
  "encryptionStats": {
    "quantum_otp": 0,
    "quantum_aes": 0,
    "post_quantum": 0,
    "standard_rsa": 0
  },
  "entropyStatus": "string",
  "averageEntropy": 0.0,
  "keyUsage": [
    {
      "date": "string",
      "keys_used": 0
    }
  ],
  "securityLevels": {
    "1": "Quantum One-Time Pad (Perfect Secrecy)",
    "2": "Quantum-Enhanced AES-256-GCM",
    "3": "Post-Quantum Cryptography (Kyber + Dilithium)",
    "4": "Standard RSA-4096 with AES-256-GCM"
  },
  "timestamp": "string",
  "systemStatus": "string"
}
```

#### Generate Quantum Keys

```
POST /api/v1/quantum/generate-keys
```

Generate quantum keys for demonstration purposes.

**Query Parameters:**
- `count` - Number of keys to generate (default: 10)

**Response:**
```json
{
  "success": true,
  "requestedKeys": 0,
  "kme1": {
    "generated": 0,
    "successful": 0,
    "failedKeys": 0,
    "successRate": 0.0
  },
  "kme2": {
    "generated": 0,
    "successful": 0,
    "failedKeys": 0,
    "successRate": 0.0
  },
  "total": {
    "generated": 0,
    "successful": 0,
    "failedKeys": 0,
    "successRate": 0.0
  },
  "keyTimestamps": [
    "string"
  ],
  "generatedAt": "string"
}
```

#### Quantum Status API

```
GET /api/v1/quantum/status
```

Get status of quantum key distribution systems.

**Response:**
```json
{
  "system_status": "string",
  "kme_servers": [
    {
      "id": 0,
      "status": "string",
      "key_count": 0,
      "entropy": 0.0
    }
  ],
  "qkd_clients": {
    "kme1": {
      "status": "string",
      "message": "string"
    },
    "kme2": {
      "status": "string",
      "message": "string"
    }
  }
}
```

#### Available Quantum Keys

```
GET /api/v1/quantum/keys/available
```

Get available quantum keys.

**Response:**
```json
{
  "keys": [
    {
      "id": "string",
      "kme": "string",
      "type": "string",
      "path": "string"
    }
  ],
  "count": 0,
  "available": true
}
```

#### Test Quantum Connection

```
POST /api/v1/quantum/test/connection
```

Test connection to quantum KME servers.

**Request Body:**
```json
{
  "kme_id": 1
}
```

**Response:**
```json
{
  "status": "string",
  "kme_id": 0,
  "sae_id": "string",
  "stored_key_count": 0,
  "total_entropy": 0.0,
  "encryption_keys_available": true,
  "timestamp": "string"
}
```

#### Exchange Quantum Key

```
POST /api/v1/quantum/key/exchange
```

Exchange a quantum key between KME servers.

**Request Body:**
```json
{
  "sender_kme_id": 1,
  "recipient_kme_id": 2
}
```

**Response:**
```json
{
  "status": "string",
  "key_id": "string",
  "key_length": 0,
  "sender_kme_id": 0,
  "recipient_kme_id": 0,
  "timestamp": "string"
}
```

### System

#### Root

```
GET /
```

Returns basic information about the API.

#### Health Check

```
GET /health
```

Check the health of the system.

**Response:**
```json
{
  "healthy": true,
  "services": {
    "database": "string",
    "km_server_1": "string",
    "km_server_2": "string",
    "security_auditor": "string"
  },
  "version": "string",
  "timestamp": "string",
  "uptime_seconds": 0.0
}
```

#### Legacy Health Check

```
GET /api/v1/health
```

Legacy health endpoint.

**Response:**
```json
{
  "status": "ok",
  "service": "QuMail Backend",
  "version": "string"
}
```

## Error Handling

Errors are returned with appropriate HTTP status codes and error messages:

```json
{
  "detail": "Error message",
  "status_code": 400,
  "error_code": "ERROR_CODE",
  "timestamp": "2023-10-16T12:00:00Z"
}
```

## Rate Limiting

API endpoints are rate-limited to prevent abuse. Current limit: 60 requests per minute per IP.

## Security Headers

All responses include comprehensive security headers for protection against common attacks.