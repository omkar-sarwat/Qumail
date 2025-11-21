# QuMail MongoDB Database Schema

## Database Information
- **Database Name**: `qumail`
- **Connection**: MongoDB Atlas (Cloud)
- **URI**: `mongodb+srv://qumail_user:******@cluster0.p6tfufc.mongodb.net/qumail`

---

## Collections

### 1. **users** Collection

Stores user account information and OAuth tokens for Gmail API access.

#### Fields:
```typescript
{
  _id: ObjectId,                    // MongoDB auto-generated ID
  id: string,                       // UUID v4 (e.g., "2c712629-0823-4605-8828-f78b99aa796c")
  email: string,                    // User's email address (unique)
  display_name: string | null,      // User's display name
  picture_url: string | null,       // Profile picture URL
  access_token: string | null,      // Google OAuth access token
  refresh_token: string | null,     // Google OAuth refresh token
  token_expiry: datetime | null,    // Access token expiration time
  created_at: datetime,             // Account creation timestamp
  last_login: datetime | null,      // Last login timestamp
  is_active: boolean                // Account active status (default: true)
}
```

#### Indexes:
- `email` (unique)
- `id` (unique)
- `created_at`

#### Example Document:
```json
{
  "_id": ObjectId("673a1234567890abcdef1234"),
  "id": "2c712629-0823-4605-8828-f78b99aa796c",
  "email": "sarswatomkar8625@gmail.com",
  "display_name": "Omkar Sarswat",
  "picture_url": "https://lh3.googleusercontent.com/...",
  "access_token": "ya29.a0AfB_byD...",
  "refresh_token": "1//0gH...",
  "token_expiry": "2025-11-17T10:30:00Z",
  "created_at": "2025-11-10T08:15:00Z",
  "last_login": "2025-11-17T09:00:00Z",
  "is_active": true
}
```

---

### 2. **emails** Collection

Stores email messages with encryption metadata.

#### Fields:
```typescript
{
  _id: ObjectId,                    // MongoDB auto-generated ID
  id: string,                       // UUID v4
  gmail_id: string,                 // Gmail message ID (unique)
  user_id: string,                  // Reference to users.id
  user_email: string,               // User's email address
  thread_id: string | null,         // Gmail thread ID
  sender: string,                   // Sender email address
  recipient: string,                // Primary recipient email
  subject: string,                  // Email subject
  body: string,                     // Email body (encrypted or plaintext)
  snippet: string | null,           // Email preview snippet
  cc: string[] | null,              // CC recipients array
  bcc: string[] | null,             // BCC recipients array
  labels: string[] | null,          // Gmail labels (e.g., ["INBOX", "UNREAD"])
  is_encrypted: boolean,            // Whether email is encrypted (default: false)
  security_level: int | null,       // Encryption level (1-4), null if not encrypted
  encryption_metadata_id: string | null, // Reference to encryption_metadata.id
  is_read: boolean,                 // Read status (default: false)
  is_starred: boolean,              // Starred status (default: false)
  is_draft: boolean,                // Draft status (default: false)
  received_at: datetime,            // Email received timestamp
  sent_at: datetime | null,         // Email sent timestamp
  created_at: datetime              // Document creation timestamp
}
```

#### Indexes:
- `gmail_id` (unique)
- `user_email`
- `user_id`
- `thread_id`
- `received_at` (descending)
- Compound: `(user_email, received_at)` (descending)

#### Example Document:
```json
{
  "_id": ObjectId("673a5678901234abcdef5678"),
  "id": "e8f3a1b2-c4d5-6e7f-8a9b-0c1d2e3f4a5b",
  "gmail_id": "18c3f5a2b1d4e6f7",
  "user_id": "2c712629-0823-4605-8828-f78b99aa796c",
  "user_email": "sarswatomkar8625@gmail.com",
  "thread_id": "18c3f5a2b1d4e6f7",
  "sender": "contact@example.com",
  "recipient": "sarswatomkar8625@gmail.com",
  "subject": "Quantum Encrypted Message",
  "body": "U2FsdGVkX1+abc123...",
  "snippet": "This is a secure quantum encrypted message...",
  "cc": [],
  "bcc": [],
  "labels": ["INBOX", "UNREAD"],
  "is_encrypted": true,
  "security_level": 2,
  "encryption_metadata_id": "meta-abc123",
  "is_read": false,
  "is_starred": false,
  "is_draft": false,
  "received_at": "2025-11-17T09:45:00Z",
  "sent_at": "2025-11-17T09:44:30Z",
  "created_at": "2025-11-17T09:45:10Z"
}
```

---

### 3. **drafts** Collection

Stores draft emails before sending.

#### Fields:
```typescript
{
  _id: ObjectId,                    // MongoDB auto-generated ID
  id: string,                       // UUID v4 (draft ID)
  user_id: string,                  // Reference to users.id
  user_email: string,               // User's email address
  recipient: string,                // Primary recipient email (to)
  subject: string,                  // Draft subject
  body: string,                     // Draft body (HTML)
  security_level: int,              // Encryption level (1-4)
  cc: string[] | null,              // CC recipients array
  bcc: string[] | null,             // BCC recipients array
  attachments: object[] | null,     // Array of attachment objects
  created_at: datetime,             // Draft creation timestamp
  updated_at: datetime,             // Draft last update timestamp
  is_synced: boolean                // Gmail sync status (default: false)
}
```

#### Attachments Object Schema:
```typescript
{
  name: string,                     // File name
  size: number,                     // File size in bytes
  type: string,                     // MIME type (e.g., "application/pdf")
  data: string                      // Base64 encoded file data
}
```

#### Indexes:
- `user_id`
- `user_email`
- `created_at`
- Compound: `(user_email, updated_at)` (descending)

#### Example Document:
```json
{
  "_id": ObjectId("673a9012345678abcdef9012"),
  "id": "f63e996a-b26f-48aa-bacb-4af232981fc1",
  "user_id": "2c712629-0823-4605-8828-f78b99aa796c",
  "user_email": "sarswatomkar8625@gmail.com",
  "recipient": "recipient@example.com",
  "subject": "Meeting Notes",
  "body": "<p>Draft content here...</p>",
  "security_level": 2,
  "cc": ["cc1@example.com"],
  "bcc": [],
  "attachments": [
    {
      "name": "document.pdf",
      "size": 245760,
      "type": "application/pdf",
      "data": "JVBERi0xLjQKJeLjz9..."
    }
  ],
  "created_at": "2025-11-17T08:30:00Z",
  "updated_at": "2025-11-17T09:15:00Z",
  "is_synced": false
}
```

---

### 4. **encryption_metadata** Collection

Stores encryption-specific metadata for decryption (IN-MEMORY CACHE - not persisted to DB in production).

#### Fields:
```typescript
{
  _id: ObjectId,                    // MongoDB auto-generated ID
  id: string,                       // Unique metadata ID
  email_id: string,                 // Reference to emails.id
  flow_id: string,                  // QKD flow ID (for quantum keys)
  key_id: string | null,            // Quantum key ID
  security_level: int,              // Encryption level (1-4)
  algorithm: string,                // Algorithm used (e.g., "OTP", "AES-256-GCM", "Kyber1024+Dilithium5")
  nonce: string | null,             // Initialization vector (base64)
  auth_tag: string | null,          // Authentication tag (base64)
  key_size: int | null,             // Key size in bytes
  created_at: datetime              // Metadata creation timestamp
}
```

#### Indexes:
- `email_id` (unique)
- `flow_id`

#### Example Document:
```json
{
  "_id": ObjectId("673adef0123456789abcdef0"),
  "id": "meta-abc123",
  "email_id": "e8f3a1b2-c4d5-6e7f-8a9b-0c1d2e3f4a5b",
  "flow_id": "flow-1731839745-abc",
  "key_id": "key-km1-001",
  "security_level": 2,
  "algorithm": "AES-256-GCM",
  "nonce": "YWJjZGVmZ2hpamts",
  "auth_tag": "bm9wcXJzdHV2d3h5eg==",
  "key_size": 32,
  "created_at": "2025-11-17T09:44:00Z"
}
```

---

### 5. **key_usage** Collection

Tracks quantum key usage for audit and compliance (IN-MEMORY CACHE - not persisted to DB in production).

#### Fields:
```typescript
{
  _id: ObjectId,                    // MongoDB auto-generated ID
  id: string,                       // UUID v4
  key_id: string,                   // Quantum key ID
  flow_id: string,                  // QKD flow ID
  kme_source: string,               // KME server (e.g., "KM1", "KM2")
  used_for: string,                 // Usage type (e.g., "encryption", "decryption")
  user_id: string,                  // Reference to users.id
  email_id: string | null,          // Reference to emails.id (if applicable)
  key_size: int,                    // Key size in bytes
  used_at: datetime,                // Usage timestamp
  success: boolean                  // Operation success status
}
```

#### Indexes:
- `key_id`
- `flow_id`
- `user_id`
- `used_at` (descending)

#### Example Document:
```json
{
  "_id": ObjectId("673af012345678901abcdef"),
  "id": "usage-xyz789",
  "key_id": "key-km1-001",
  "flow_id": "flow-1731839745-abc",
  "kme_source": "KM1",
  "used_for": "encryption",
  "user_id": "2c712629-0823-4605-8828-f78b99aa796c",
  "email_id": "e8f3a1b2-c4d5-6e7f-8a9b-0c1d2e3f4a5b",
  "key_size": 256,
  "used_at": "2025-11-17T09:44:00Z",
  "success": true
}
```

---

### 6. **attachments** Collection

Stores email attachments with encryption support.

#### Fields:
```typescript
{
  _id: ObjectId,                    // MongoDB auto-generated ID
  id: string,                       // UUID v4
  email_id: string,                 // Reference to emails.id
  filename: string,                 // Original filename
  content_type: string,             // MIME type
  size: int,                        // File size in bytes
  data: string,                     // Base64 encoded file data (encrypted or plaintext)
  is_encrypted: boolean,            // Whether attachment is encrypted
  encryption_key: string | null,    // Encryption key (base64) if encrypted
  encryption_nonce: string | null,  // Nonce/IV (base64) if encrypted
  created_at: datetime              // Attachment creation timestamp
}
```

#### Indexes:
- `email_id`
- `created_at`

#### Example Document:
```json
{
  "_id": ObjectId("673a1122334455667788aabb"),
  "id": "attach-def456",
  "email_id": "e8f3a1b2-c4d5-6e7f-8a9b-0c1d2e3f4a5b",
  "filename": "report.pdf",
  "content_type": "application/pdf",
  "size": 524288,
  "data": "U2FsdGVkX1+encrypted_data_here...",
  "is_encrypted": true,
  "encryption_key": "a2V5X2VuY3J5cHRlZA==",
  "encryption_nonce": "bm9uY2VfZW5jcnlwdGVk",
  "created_at": "2025-11-17T09:44:00Z"
}
```

---

## Security Levels

QuMail supports 4 levels of quantum encryption:

1. **Level 1 - OTP (One-Time Pad)**
   - Pure quantum key encryption
   - Uses quantum keys from KME servers
   - Algorithm: XOR with quantum key

2. **Level 2 - AES-256-GCM**
   - Quantum-enhanced AES encryption
   - Uses quantum keys as AES encryption keys
   - Algorithm: AES-256-GCM with quantum-derived keys

3. **Level 3 - Post-Quantum Cryptography (PQC)**
   - NIST-approved post-quantum algorithms
   - Kyber1024 (key encapsulation) + Dilithium5 (digital signatures)
   - Optional quantum enhancement

4. **Level 4 - RSA-4096 + AES-256**
   - Hybrid classical encryption
   - RSA-4096 for key exchange, AES-256-GCM for content
   - Optional quantum enhancement

---

## Relationships

```
users (1) ──────────────────── (*) emails
  |                                  |
  |                                  |
  └─────── (*) drafts                ├─── (1) encryption_metadata
                                     |
                                     └─── (*) attachments

users (1) ──────────────────── (*) key_usage
                                     |
                                     └─── relates to ──> encryption_metadata
```

---

## Data Flow

### Email Send Flow:
1. User composes email in frontend
2. Select security level (1-4)
3. Backend encrypts content using quantum keys (if level 1-2)
4. Encryption metadata stored in `encryption_metadata` collection
5. Email sent via Gmail API
6. Email record stored in `emails` collection with `is_encrypted=true`
7. Key usage logged in `key_usage` collection

### Email Decrypt Flow:
1. User requests email decryption
2. Backend retrieves `encryption_metadata` by `email_id`
3. Backend retrieves quantum keys using `flow_id` from KME
4. Decrypts content using appropriate algorithm
5. Returns plaintext to frontend

### Draft Save Flow:
1. User composes email and clicks "Save Draft"
2. Frontend sends FormData to `POST /api/v1/emails/drafts`
3. Backend checks if draft exists by `id`
4. If exists, updates; if not, creates new draft
5. Draft stored in `drafts` collection
6. Returns draft ID to frontend

---

## Notes

- **In-Memory Cache**: `encryption_metadata` and `key_usage` collections are primarily used in-memory for performance. Database storage is fallback only.
- **Quantum Keys**: Keys are retrieved from Next Door Key Simulator (ETSI QKD 014 standard) via KME1 and KME2.
- **Gmail Sync**: All emails are synced with Gmail via Gmail API. QuMail acts as a secure layer on top of Gmail.
- **ObjectId vs UUID**: MongoDB uses `_id` (ObjectId) as primary key, but application uses `id` (UUID) for cross-platform compatibility.
- **Datetime Format**: All timestamps are stored in UTC using Python's `datetime.utcnow()`.
- **Security**: Access tokens and refresh tokens are stored encrypted in the database. Never expose them in API responses.

---

## Database Initialization

To initialize the database with collections and indexes:

```bash
cd qumail-backend
python push_to_mongodb.py
```

This script:
- Connects to MongoDB Atlas
- Creates all collections
- Sets up indexes
- Runs test queries
- Displays database statistics
