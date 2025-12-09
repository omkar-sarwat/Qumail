# Per-User Key Pool Implementation Summary

## Overview

This implementation adds a comprehensive **Two-Tier Key Manager System** to the Next Door Key Simulator following **ETSI GS QKD 014** standards. The system provides:

- **Per-user key pools** with complete isolation between users
- **1KB (1024 bytes)** quantum keys as required by ETSI standard
- **Sender requests keys FROM receiver's pool** (proper QKD flow)
- **Local Key Manager** caching layer for high availability
- **Hybrid sync strategy** (scheduled + threshold-based emergency)

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     QuMail Application                          │
└─────────────────────┬───────────────────────────────────────────┘
                      │ ETSI GS QKD 014 API
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Local Key Manager (LKM)                        │
│  • Per-user key pool caching                                    │
│  • Always available (even if remote KM offline)                 │
│  • Hybrid sync: daily scheduled + threshold-based emergency     │
└─────────────────────┬───────────────────────────────────────────┘
                      │ Sync Protocol
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                Next Door Key Manager (Remote)                    │
│  • Quantum key generation                                       │
│  • ETSI QKD 014 compliant                                       │
└─────────────────────────────────────────────────────────────────┘
```

## Files Created/Modified

### New Files

1. **`keys/user_key_pool.py`** (738 lines)
   - `UserKeyPool` class with SQLite persistence
   - Per-user key pool management
   - Key generation, delivery, and tracking
   - Core methods:
     - `register_user()` - Create user and key pool
     - `get_keys_for_receiver()` - Get keys from receiver's pool (enc_keys)
     - `get_keys_by_ids()` - Retrieve specific keys (dec_keys)
     - `get_pool_status()` - Pool statistics
     - `refill_pool()` - Add more keys
     - `delete_user()` - Remove user and all keys

2. **`keys/local_key_manager.py`** (507 lines)
   - `LocalKeyManager` class with sync capability
   - Background sync worker thread
   - Emergency threshold handling
   - ETSI API methods:
     - `get_enc_keys()` - Encryption key delivery
     - `get_dec_keys()` - Decryption key retrieval
     - `get_status()` - Pool status
     - `get_km_status()` - Overall KM status

3. **`router/user_keys.py`** (472 lines)
   - Flask Blueprint with ETSI GS QKD 014 endpoints
   - Routes:
     - `POST /api/v1/keys/register`
     - `POST /api/v1/keys/{SAE_ID}/enc_keys`
     - `POST /api/v1/keys/{SAE_ID}/dec_keys`
     - `GET /api/v1/keys/{SAE_ID}/status`
     - `POST /api/v1/keys/{SAE_ID}/refill`
     - `DELETE /api/v1/keys/{SAE_ID}`
     - `GET /api/v1/keys/pools`
     - `GET /api/v1/keys/km/status`
     - `POST /api/v1/keys/km/sync`

4. **`keys/__init__.py`** - Module exports
5. **`router/__init__.py`** - Router module exports
6. **`test_user_key_pools.py`** - Comprehensive test suite
7. **`test_simple_key_pools.py`** - Simple test suite
8. **`RUN_USER_POOL_TESTS.ps1`** - PowerShell test runner

### Modified Files

1. **`app.py`**
   - Added imports for new modules
   - Added `/health` endpoint
   - Integrated Local KM startup/shutdown
   - Registered user_keys routes

## Key Features

### 1. Per-User Key Pools

Each user (identified by SAE_ID) has:
- Isolated key pool (no sharing between users)
- SQLite-backed persistence
- Configurable pool size (default: 1000 keys)
- Low threshold warnings (default: 10%)
- Automatic refill capability

### 2. 1KB Key Size (ETSI Compliant)

```python
KEY_SIZE_BYTES = 1024  # 1KB
KEY_SIZE_BITS = 8192   # 8192 bits
```

All quantum keys are exactly 1KB as per ETSI GS QKD 014.

### 3. Cross-User Key Request

**Critical Flow:** Sender requests keys FROM receiver's pool

```
Alice (sender) wants to send encrypted email to Bob (receiver)
    │
    ▼
Alice calls: POST /api/v1/keys/BOB_SAE_ID/enc_keys
    │         Headers: X-SAE-ID: ALICE_SAE_ID
    │
    ▼
System retrieves keys from BOB's pool (not Alice's)
    │
    ▼
Keys are marked as "used" and "delivered_to: ALICE"
    │
    ▼
Alice encrypts message with keys
    │
    ▼
Bob receives encrypted message with key IDs
    │
    ▼
Bob calls: POST /api/v1/keys/BOB_SAE_ID/dec_keys
           with key_IDs from the message
    │
    ▼
System returns the same keys to Bob for decryption
```

### 4. Key ID Format

```
qk_{SAE_ID}_{sequence_number:06d}

Example: qk_SAE_ALICE_000001
```

### 5. Database Schema

```sql
-- Users table
CREATE TABLE users (
    sae_id TEXT PRIMARY KEY,
    user_email TEXT UNIQUE,
    display_name TEXT,
    registered_at TEXT,
    is_active INTEGER DEFAULT 1,
    last_activity TEXT
);

-- Key pools metadata
CREATE TABLE key_pools (
    pool_id INTEGER PRIMARY KEY,
    sae_id TEXT UNIQUE,
    total_keys INTEGER DEFAULT 0,
    used_keys INTEGER DEFAULT 0,
    available_keys INTEGER DEFAULT 0,
    last_sync_time TEXT,
    pool_size_limit INTEGER DEFAULT 1000,
    low_threshold INTEGER DEFAULT 100
);

-- Quantum keys
CREATE TABLE quantum_keys (
    key_id TEXT PRIMARY KEY,
    sae_id TEXT,
    key_data BLOB,
    key_size INTEGER DEFAULT 1024,
    status TEXT DEFAULT 'unused',
    created_at TEXT,
    used_at TEXT,
    delivered_to_sae_id TEXT,
    delivered_at TEXT
);
```

### 6. Sync Strategy

**Hybrid Approach:**
- **Scheduled sync:** Every 24 hours (configurable)
- **Threshold sync:** When pool drops below 10%
- **Emergency sync:** When pool drops below 5%

### 7. One-Time Use Enforcement

Keys are immediately marked as `used` upon delivery and cannot be reused.

## API Examples

### Register User
```http
POST /api/v1/keys/register
Content-Type: application/json

{
    "sae_id": "SAE_ALICE_001",
    "user_email": "alice@example.com",
    "initial_pool_size": 1000
}
```

### Get Encryption Keys
```http
POST /api/v1/keys/SAE_BOB_001/enc_keys
X-SAE-ID: SAE_ALICE_001
Content-Type: application/json

{
    "number": 5,
    "size": 8192
}
```

### Get Decryption Keys
```http
POST /api/v1/keys/SAE_ALICE_001/dec_keys
X-SAE-ID: SAE_BOB_001
Content-Type: application/json

{
    "key_IDs": [
        {"key_ID": "qk_SAE_BOB_001_000001"},
        {"key_ID": "qk_SAE_BOB_001_000002"}
    ]
}
```

### Check Pool Status
```http
GET /api/v1/keys/SAE_ALICE_001/status
```

## Testing

### Run Tests
```powershell
cd next-door-key-simulator
.\RUN_USER_POOL_TESTS.ps1
```

Or manually:
```powershell
# Terminal 1: Start server
python app.py

# Terminal 2: Run tests
python test_simple_key_pools.py
```

### Test Coverage
1. User registration
2. Key size validation (1KB)
3. Cross-user key request
4. Pool isolation
5. Pool exhaustion handling
6. One-time use enforcement
7. Decryption key retrieval
8. Status endpoints
9. Pool refill mechanism

## Configuration

Environment variables:
```bash
KME_ID=1                              # KME instance ID
HOST=127.0.0.1                        # Server host
PORT=8010                             # Server port
USE_HTTPS=false                       # Enable HTTPS
LOCAL_KM_ID=LOCAL_KM_001              # Local KM identifier
NEXT_DOOR_KM_URL=http://localhost:8010  # Remote KM URL
USER_KEY_POOL_DB=user_key_pools.db    # SQLite database path
MAX_KEYS_PER_REQUEST=100              # Max keys per request
```

## Compliance

This implementation follows:
- **ETSI GS QKD 014** - Quantum Key Distribution (QKD) Protocol and data format for quantum secured networks
- Key size: 1024 bytes (8192 bits)
- REST API format for key delivery
- SAE_ID-based identification
