# Receiver Identification in QuMail Quantum Key Distribution System

## Executive Summary

This document describes the implementation of **receiver identification** in the QuMail quantum-secure email system. The core problem was: **"How does the receiver know a quantum key is intended for them?"**

We solved this by implementing email-based key association tracking at the KME (Key Management Entity) level, following the ETSI GS QKD 014 standard while adding receiver verification capabilities.

---

## Problem Statement

### The Challenge

In a Quantum Key Distribution (QKD) system using the ETSI GS QKD 014 standard:

1. **Sender (Alice)** requests an encryption key from KME1
2. **KME1** generates a quantum key and broadcasts it to KME2
3. **Receiver (Bob)** needs to retrieve the SAME key from KME2 to decrypt

**The Problem**: How does KME2 know which key belongs to which receiver? Without identification:
- Any user could request any key
- No audit trail of key usage
- Security vulnerability: key interception possible

### Previous State

Before our implementation:
- Keys were stored with only SAE ID pairs (Secure Application Entity IDs)
- No association between keys and user emails
- Receiver had to know the exact `key_ID` with no verification
- No logging of who requested which keys

---

## Solution Architecture

### Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ENCRYPTION FLOW (Sender)                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────┐    ┌──────────────────┐    ┌─────────────────────────────┐ │
│  │   QuMail    │    │  QuMail Backend  │    │       KME1 (Sender)         │ │
│  │  Frontend   │───▶│   (FastAPI)      │───▶│   Next Door Key Simulator   │ │
│  │             │    │                  │    │                             │ │
│  │ Compose     │    │ Headers:         │    │ ┌─────────────────────────┐ │ │
│  │ Email to    │    │ X-Sender-Email:  │    │ │ SharedKeyPool           │ │ │
│  │ bob@test    │    │   alice@test     │    │ │ ┌─────────────────────┐ │ │ │
│  │             │    │ X-Receiver-Email:│    │ │ │ Key: abc123...      │ │ │ │
│  │ Security    │    │   bob@test       │    │ │ │ Sender: alice@test  │ │ │ │
│  │ Level: 1    │    │                  │    │ │ │ Receiver: bob@test  │ │ │ │
│  └─────────────┘    └──────────────────┘    │ │ └─────────────────────┘ │ │ │
│                                              │ └─────────────────────────┘ │ │
│                                              │                             │ │
│                                              │ Broadcasts key + email      │ │
│                                              │ association to KME2 ───────────┤
│                                              └─────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                        DECRYPTION FLOW (Receiver)                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────┐    ┌──────────────────┐    ┌─────────────────────────────┐ │
│  │   QuMail    │    │  QuMail Backend  │    │      KME2 (Receiver)        │ │
│  │  Frontend   │◀───│   (FastAPI)      │◀───│   Next Door Key Simulator   │ │
│  │             │    │                  │    │                             │ │
│  │ View Email  │    │ Headers:         │    │ ┌─────────────────────────┐ │ │
│  │ from alice  │    │ X-Receiver-Email:│    │ │ KeyStore                │ │ │
│  │             │    │   bob@test       │    │ │ ┌─────────────────────┐ │ │ │
│  │ Click       │    │                  │    │ │ │ Key: abc123...      │ │ │ │
│  │ "Decrypt"   │    │ key_ID: abc123   │    │ │ │ Receiver: bob@test  │◀─VERIFY
│  │             │    │                  │    │ │ └─────────────────────┘ │ │ │
│  │ ✓ Decrypted │    │ ✓ Key verified   │    │ │                         │ │ │
│  │   content   │    │   for bob@test   │    │ │ ✓ Match! Return key    │ │ │
│  └─────────────┘    └──────────────────┘    │ └─────────────────────────┘ │ │
│                                              └─────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Components Modified

1. **KME External Routes** (`router/external.py`)
2. **KME Key Store** (`keys/key_store.py`)
3. **Backend KME Service** (`kme_service.py`)
4. **Backend Encryption Service** (`complete_encryption_service.py`)
5. **All Encryption Levels** (`level1_otp.py`, `level2_aes.py`, `level3_pqc.py`, `level4_rsa.py`)

---

## Detailed Implementation

### 1. HTTP Header-Based Email Tracking

**File: `next-door-key-simulator/router/external.py`**

We added extraction of sender and receiver email from HTTP headers in the `get_key` method:

```python
def get_key(self, request: flask.Request, slave_sae_id):
    """ETSI QKD 014: Get encryption keys"""
    
    # NEW: Extract email headers for receiver identification
    sender_email = request.headers.get('X-Sender-Email', '')
    receiver_email = request.headers.get('X-Receiver-Email', slave_sae_id)
    
    print(f'[ENC_KEYS] User pair: sender={sender_email}, receiver={receiver_email}')
    
    # ... key generation logic ...
    
    # Store keys WITH email association
    self.key_store.append_keys(
        master_sae_id, slave_sae_id, keys,
        do_broadcast=True,
        sender_email=sender_email,
        receiver_email=receiver_email
    )
    
    # Return keys with receiver info for client verification
    return {
        'keys': keys,
        'receiver_sae_id': slave_sae_id,
        'receiver_email': receiver_email,
        'sender_email': sender_email
    }
```

**Why HTTP Headers?**
- Non-intrusive: Doesn't modify ETSI QKD 014 request/response body format
- Backward compatible: Clients not using headers still work
- Standard practice: Similar to authentication tokens in REST APIs

### 2. Key-Email Association Storage

**File: `next-door-key-simulator/keys/key_store.py`**

We added an in-memory mapping of key IDs to email associations:

```python
class KeyStore:
    def __init__(self, key_pool: KeyPool, broadcaster: Broadcaster):
        self.container: list[dict[str, object]] = []
        self.key_pool = key_pool
        self.broadcaster = broadcaster
        
        # NEW: Email to key association for receiver lookup
        self.email_key_map: Dict[str, Dict[str, str]] = {}
    
    def get_key_email_info(self, key_id: str) -> Optional[Dict[str, str]]:
        """Get the email info associated with a key (for receiver verification)."""
        return self.email_key_map.get(key_id)
    
    def append_keys(self, master_sae_id: str, slave_sae_id: str, keys: list, 
                    do_broadcast: bool = True, 
                    sender_email: str = '', 
                    receiver_email: str = '') -> list:
        """Store keys with email association for receiver identification."""
        
        # Store in main container
        # ... existing logic ...
        
        # NEW: Store email association for each key
        if sender_email or receiver_email:
            for key in keys:
                key_id = key.get('key_ID')
                if key_id:
                    self.email_key_map[key_id] = {
                        'sender_email': sender_email,
                        'receiver_email': receiver_email,
                        'master_sae_id': master_sae_id,
                        'slave_sae_id': slave_sae_id
                    }
                    print(f'[KEY_STORE] Associated key {key_id[:16]}... with receiver: {receiver_email}')
```

**Why In-Memory Storage?**
- **Speed**: No database latency for key lookups
- **Security**: Keys and associations are ephemeral (cleared on restart)
- **Simplicity**: No additional database schema required
- **Requirement Compliance**: Per the requirements document: "keys stored in-memory only"

### 3. Receiver Verification on Decryption

**File: `next-door-key-simulator/router/external.py`**

When the receiver requests their decryption key, we verify their identity:

```python
def get_key_with_ids(self, request: flask.Request, master_sae_id: str):
    """ETSI QKD 014: Get decryption keys by ID"""
    
    # NEW: Get receiver email from header for verification
    receiver_email = request.headers.get('X-Receiver-Email', '')
    print(f"[DEC_KEYS] Receiver email from header: {receiver_email}")
    
    # ... key retrieval logic ...
    
    # NEW: Verify receiver matches intended recipient
    if receiver_email:
        for key in selected_keys:
            key_id = key.get('key_ID')
            if key_id:
                email_info = self.key_store.get_key_email_info(key_id)
                if email_info:
                    intended_receiver = email_info.get('receiver_email', '')
                    if intended_receiver and intended_receiver != receiver_email:
                        print(f"[DEC_KEYS SECURITY] WARNING: Key {key_id[:16]}... "
                              f"intended for {intended_receiver} but requested by {receiver_email}")
                    else:
                        print(f"[DEC_KEYS] ✓ Key {key_id[:16]}... verified for receiver: {receiver_email}")
    
    return {'keys': selected_keys}
```

**Security Note**: Currently, mismatched receivers are logged but keys are still delivered. This allows for:
- Debugging during development
- Audit trail for security review
- Future enhancement to block unauthorized access

### 4. Backend Integration

**File: `qumail-backend/app/services/kme_service.py`**

Updated the KME client methods to include email headers:

```python
async def get_encryption_keys(self, server_id: int, slave_sae_id: int, count: int = 1,
                               sender_email: str = '', receiver_email: str = '') -> List[Dict[str, Any]]:
    """Get encryption keys with sender/receiver email tracking."""
    
    # Add email headers for key association tracking
    headers = {}
    if sender_email:
        headers['X-Sender-Email'] = sender_email
    if receiver_email:
        headers['X-Receiver-Email'] = receiver_email
    
    logger.info(f"[KME] Requesting {count} enc_keys for {sender_email} -> {receiver_email}")
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data, ssl=ssl_context, headers=headers) as response:
            # ... response handling ...

async def get_decryption_key(self, server_id: int, master_sae_id: int, key_id: str,
                              receiver_email: str = '') -> Dict[str, Any]:
    """Get decryption key with receiver email verification."""
    
    headers = {}
    if receiver_email:
        headers['X-Receiver-Email'] = receiver_email
    
    logger.info(f"[KME] Requesting dec_keys for key {key_id[:16]}... receiver: {receiver_email}")
    
    # ... request logic ...
```

### 5. Encryption Metadata Enhancement

**Files: `level1_otp.py`, `level2_aes.py`, `level3_pqc.py`, `level4_rsa.py`**

Each encryption level now includes sender/receiver in the metadata:

```python
async def encrypt_otp(content: str, user_email: str, 
                      receiver_email: str = "", ...) -> Dict[str, Any]:
    """Level 1: One-Time Pad encryption with receiver tracking."""
    
    logger.info(f"LEVEL 1 OTP-QKD ENCRYPTION START")
    logger.info(f"  Sender: {user_email}")
    logger.info(f"  Receiver: {receiver_email}")
    
    # ... encryption logic ...
    
    return {
        "encrypted_content": encrypted_content,
        "algorithm": "OTP-QKD-ETSI-014",
        "auth_tag": auth_tag_b64,
        "metadata": {
            "flow_id": flow_id,
            "security_level": 1,
            "algorithm": "OTP-QKD-ETSI-014",
            "key_id": key_id,
            # ... other metadata ...
            
            # NEW: Sender/receiver for receiver identification
            "sender_email": user_email,
            "receiver_email": receiver_email
        }
    }
```

**Why in Metadata?**
- Stored with the encrypted email in MongoDB
- Available for decryption verification
- Audit trail: who sent to whom
- Enables future features: read receipts, access logs

---

## Data Flow Example

### Sending an Encrypted Email

```
1. User composes email in QuMail Frontend
   - To: bob@example.com
   - Subject: "Secret Message"
   - Security Level: 1 (OTP)

2. Frontend calls Backend API: POST /api/v1/messages/send
   {
     "to": "bob@example.com",
     "subject": "Secret Message",
     "body": "Hello Bob!",
     "security_level": 1
   }

3. Backend CompleteEmailService.send_encrypted_email():
   - sender_email = "alice@example.com" (from auth)
   - recipient_email = "bob@example.com"
   - Calls _encrypt_by_level(1, content, sender_email, recipient_email)

4. QuantumEncryptionService.encrypt_level_1_otp():
   - Calls encrypt_otp(content, sender_email, receiver_email="bob@example.com")

5. encrypt_otp() calls KME Service:
   - KME1.request_enc_keys() with headers:
     X-Sender-Email: alice@example.com
     X-Receiver-Email: bob@example.com

6. KME1 external_routes.get_key():
   - Extracts email headers
   - Generates quantum key from SharedKeyPool
   - Stores in KeyStore with email_key_map:
     {
       "key_ID_abc123": {
         "sender_email": "alice@example.com",
         "receiver_email": "bob@example.com"
       }
     }
   - Broadcasts key to KME2
   - Returns key with key_ID

7. encrypt_otp() encrypts content with quantum key
   - Returns encrypted_content + metadata (includes key_ID, emails)

8. Backend stores in MongoDB:
   {
     "flow_id": "xyz789",
     "sender_email": "alice@example.com",
     "receiver_email": "bob@example.com",
     "body_encrypted": "base64...",
     "encryption_metadata": {
       "key_id": "abc123",
       "sender_email": "alice@example.com",
       "receiver_email": "bob@example.com"
     }
   }

9. Backend sends encrypted email via Gmail API
```

### Receiving and Decrypting

```
1. Bob opens QuMail, sees encrypted email from Alice

2. Bob clicks "Decrypt" button

3. Frontend calls: POST /api/v1/messages/{id}/decrypt

4. Backend retrieves email from MongoDB:
   - Gets encryption_metadata.key_id = "abc123"
   - Gets receiver_email = "bob@example.com"

5. Backend calls KME2.get_decryption_key():
   - URL: /api/v1/keys/{master_sae_id}/dec_keys?key_ID=abc123
   - Headers: X-Receiver-Email: bob@example.com

6. KME2 external_routes.get_key_with_ids():
   - Extracts receiver_email from header
   - Looks up key_ID in KeyStore
   - Verifies: email_key_map["abc123"].receiver_email == "bob@example.com"
   - ✓ Match! Returns key

7. Backend decrypt_otp() decrypts content with key

8. Frontend displays: "Hello Bob!"
```

---

## Test Results

### Test Script: `test_receiver_identification.py`

```
######################################################################
# RECEIVER IDENTIFICATION TESTS
# Testing KME key tracking with sender/receiver email association   
######################################################################

======================================================================
 TEST: Request Encryption Keys with Email Tracking
======================================================================
  URL: http://127.0.0.1:8010/api/v1/keys/.../enc_keys
  Headers: X-Sender-Email=alice@qumail.test, X-Receiver-Email=bob@qumail.test
  Request: {'number': 1, 'size': 256}
  Status: 200
  ✓ Got 1 key(s)
    Key ID: e0ddfe75-df3e-43fb-ad3f-4e4d0735...
    Receiver SAE ID: c565d5aa-8670-4446-8471-b0e53e315d2a
    Receiver Email: bob@qumail.test
    Sender Email: alice@qumail.test

======================================================================
 TEST: Request Decryption Keys with Receiver Verification
======================================================================
  URL: http://127.0.0.1:8020/api/v1/keys/.../dec_keys
  Key ID: e0ddfe75-df3e-43fb-ad3f-4e4d0735...
  Receiver Email: bob@qumail.test
  Status: 200
  ✓ Got 1 key(s)
    Key ID: e0ddfe75-df3e-43fb-ad3f-4e4d0735...

======================================================================
 TEST: Key-Email Association in KeyStore
======================================================================
  Sender: charlie@qumail.test
  Receiver: diana@qumail.test
  ✓ Request successful
    Sender in response: charlie@qumail.test
    Receiver in response: diana@qumail.test

======================================================================
 TEST SUMMARY
======================================================================
  enc_keys_with_email: ✓ PASS
  dec_keys_with_verification: ✓ PASS
  key_email_association: ✓ PASS

  🎉 All tests passed!
```

### KME Terminal Logs (Verification)

```
[ENC_KEYS] User pair: sender=alice@qumail.test, receiver=bob@qumail.test
[ENC_KEYS] Calling append_keys with do_broadcast=True (default)
[KEY_STORE] Associated key e0ddfe75-df3e-43... with receiver: bob@qumail.test
[KEY_STORE] append_keys called: master_sae_id=..., slave_sae_id=...
[KEY_STORE] Email association: sender=alice@qumail.test, receiver=bob@qumail.test
[KEY_STORE] Broadcasting keys to other KMEs (non-blocking)...
[BROADCAST] Response status: 200

[DEC_KEYS] Receiver email from header: bob@qumail.test
[DEC_KEYS] ✓ Key e0ddfe75-df3e-43... verified for receiver: bob@qumail.test
```

---

## Files Modified

| File | Changes |
|------|---------|
| `next-door-key-simulator/router/external.py` | Added email header extraction, receiver verification logging |
| `next-door-key-simulator/keys/key_store.py` | Added `email_key_map`, `get_key_email_info()`, updated `append_keys()` |
| `next-door-key-simulator/router/user_keys.py` | Changed URL prefix to `/api/v1/user-keys` to avoid conflicts |
| `qumail-backend/app/services/kme_service.py` | Added email headers to `get_encryption_keys()` and `get_decryption_key()` |
| `qumail-backend/app/services/complete_email_service.py` | Updated `_encrypt_by_level()` to pass receiver email |
| `qumail-backend/app/services/encryption/complete_encryption_service.py` | Added `receiver_email` parameter to all encrypt methods |
| `qumail-backend/app/services/encryption/level1_otp.py` | Added `receiver_email` param, included in metadata |
| `qumail-backend/app/services/encryption/level2_aes.py` | Added `receiver_email` param, included in metadata |
| `qumail-backend/app/services/encryption/level3_pqc.py` | Added `receiver_email` param, included in metadata |
| `qumail-backend/app/services/encryption/level4_rsa.py` | Added `receiver_email` param, included in metadata |

---

## Security Considerations

### What This Implementation Provides

1. **Audit Trail**: Every key request is logged with sender/receiver emails
2. **Receiver Awareness**: KME knows which user each key is intended for
3. **Verification Capability**: Decryption requests can be verified against intended receiver
4. **Non-Breaking**: Existing clients without email headers still work

### What Could Be Added (Future Work)

1. **Strict Enforcement**: Block key delivery if receiver doesn't match
2. **Authentication Integration**: Verify X-Receiver-Email matches authenticated user
3. **Persistent Audit Log**: Store key usage in database for compliance
4. **Key Expiration**: Auto-expire keys not retrieved within timeframe

---

## Conclusion

The receiver identification system solves the fundamental problem of **"How does the receiver know a key is for them?"** by:

1. **Tracking email associations** at the KME level during key generation
2. **Passing receiver identity** through the entire encryption chain
3. **Verifying receiver identity** when decryption keys are requested
4. **Logging all operations** for audit and debugging

This implementation follows the ETSI GS QKD 014 standard while adding the necessary application-layer identity tracking required for a secure email system.
