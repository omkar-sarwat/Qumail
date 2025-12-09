"""MongoDB document models using Pydantic for validation."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
import uuid

class EmailDirection(str, Enum):
    SENT = "SENT"
    RECEIVED = "RECEIVED"

class UserDocument(BaseModel):
    """User document model for MongoDB."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    email: str
    display_name: Optional[str] = None
    password_hash: Optional[str] = None  # Hashed password for login
    oauth_access_token: Optional[str] = None
    oauth_refresh_token: Optional[str] = None
    oauth_token_expiry: Optional[datetime] = None
    session_token: Optional[str] = None
    # Yahoo OAuth tokens
    yahoo_tokens: Optional[Dict[str, Any]] = None  # {access_token, refresh_token, expires_at, email}
    # Microsoft OAuth tokens  
    microsoft_tokens: Optional[Dict[str, Any]] = None  # {access_token, refresh_token, expires_at, email}
    # TOTP 2FA fields
    totp_secret: Optional[str] = None  # Encrypted TOTP secret for Google Authenticator
    totp_enabled: bool = False  # Whether 2FA is enabled
    totp_verified: bool = False  # Whether user has verified their 2FA setup
    backup_codes: Optional[List[str]] = None  # Encrypted backup codes (single-use)
    backup_codes_used: Optional[List[str]] = None  # Track which backup codes have been used
    # Crypto keys
    rsa_public_key_pem: Optional[str] = None
    rsa_private_key_pem: Optional[str] = None
    kyber_public_key: Optional[bytes] = None
    kyber_private_key: Optional[bytes] = None
    dilithium_public_key: Optional[bytes] = None
    dilithium_private_key: Optional[bytes] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    
    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}

class EmailDocument(BaseModel):
    """Email document model for MongoDB."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    flow_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    sender_email: str
    receiver_email: str
    allowed_emails: Optional[List[str]] = None
    subject: Optional[str] = None
    body_encrypted: Optional[str] = None
    decrypted_body: Optional[str] = None  # Cached plaintext after first decryption
    encryption_key_id: Optional[str] = None
    encryption_algorithm: Optional[str] = None
    encryption_iv: Optional[str] = None
    encryption_auth_tag: Optional[str] = None
    encryption_metadata: Optional[Dict[str, Any]] = None
    # Explicit public key fields for Level 3 and 4 (stored in MongoDB, private keys stay local)
    rsa_public_key: Optional[str] = None  # Level 4: RSA-4096 public key (PEM, base64)
    kem_public_key: Optional[str] = None  # Level 3: ML-KEM-1024 public key (base64)
    dsa_public_key: Optional[str] = None  # Level 3: ML-DSA-87 public key (base64)
    private_key_ref: Optional[str] = None  # Reference ID for local private key lookup
    security_level: int = 0
    direction: EmailDirection
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    is_read: bool = False
    is_starred: bool = False
    is_suspicious: bool = False
    gmail_message_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}

class DraftDocument(BaseModel):
    """Draft document model for MongoDB - synced across devices via user's Google account."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    user_id: str = Field(..., min_length=1, description="Required: MongoDB user ID")
    user_email: str = Field(..., min_length=1, description="Required: User's email address")
    recipient: Optional[str] = ""
    subject: Optional[str] = ""
    body: Optional[str] = ""
    security_level: int = Field(default=2, ge=1, le=4)
    cc: Optional[str] = None
    bcc: Optional[str] = None
    attachments: Optional[List[str]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_synced: bool = True  # Synced across devices
    device_info: Optional[str] = None  # Optional: track which device created the draft
    
    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}
    
    def dict(self, **kwargs):
        """Override dict to ensure _id is used for MongoDB."""
        d = super().dict(**kwargs)
        # Ensure _id is used instead of id when by_alias=True
        if kwargs.get('by_alias') and 'id' in d and '_id' not in d:
            d['_id'] = d.pop('id')
        return d

class EncryptionMetadataDocument(BaseModel):
    """Encryption metadata document model for MongoDB."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    flow_id: str
    email_id: Optional[str] = None
    security_level: int
    algorithm: str
    key_id: Optional[str] = None
    key_ids: Optional[Dict[str, str]] = None
    nonce: Optional[str] = None
    auth_tag: Optional[str] = None
    signature: Optional[str] = None
    quantum_enhanced: bool = True
    encrypted_size: Optional[int] = None
    additional_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}

class KeyUsageDocument(BaseModel):
    """Key usage tracking document model for MongoDB."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    email_id: str
    key_id: str
    algorithm: str
    key_size: int
    entropy_score: float = 0.0
    source_kme: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}

class AttachmentDocument(BaseModel):
    """Attachment document model for MongoDB."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    email_id: str
    filename: str
    content_type: str
    size: int
    encrypted_data: Optional[str] = None
    decrypted_content: Optional[str] = None  # Cached decrypted content
    security_level: Optional[int] = None
    flow_id: Optional[str] = None
    encryption_algorithm: Optional[str] = None
    encryption_metadata: Optional[Dict[str, Any]] = None
    encryption_key_id: Optional[str] = None
    encryption_auth_tag: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}


# ============================================================================
# QKD (Quantum Key Distribution) MongoDB Models
# ============================================================================

class QKDKeyState(str, Enum):
    """State of a quantum key in its lifecycle."""
    READY = "ready"           # Key is available for use
    RESERVED = "reserved"     # Key is reserved but not yet consumed
    CONSUMED = "consumed"     # Key has been used (one-time use)
    EXPIRED = "expired"       # Key has expired
    REVOKED = "revoked"       # Key was manually revoked


class QKDKeyDocument(BaseModel):
    """
    Quantum Key Distribution key document for MongoDB.
    Stores quantum keys retrieved from KME servers with full lifecycle tracking.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    
    # Key identifiers
    key_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    kme1_key_id: Optional[str] = None  # Key ID from KME1 (Alice)
    kme2_key_id: Optional[str] = None  # Key ID from KME2 (Bob)
    
    # Key material (base64 encoded, encrypted at rest)
    key_material_encrypted: Optional[str] = None  # Encrypted key material
    key_hash: Optional[str] = None  # SHA-256 hash for integrity verification
    key_size_bits: int = 256  # Key size in bits
    
    # Source information
    source_kme: str = "KME1"  # Which KME the key came from (KME1 or KME2)
    sae1_id: Optional[str] = None  # SAE ID for KME1 (sender)
    sae2_id: Optional[str] = None  # SAE ID for KME2 (receiver)
    
    # User association
    sender_email: Optional[str] = None  # Email of sender who requested key
    receiver_email: Optional[str] = None  # Email of intended receiver
    flow_id: Optional[str] = None  # Associated encryption flow ID
    email_id: Optional[str] = None  # Associated email ID
    
    # Security level
    security_level: int = 1  # 1=OTP, 2=AES, 3=PQC, 4=RSA
    algorithm: Optional[str] = None  # Encryption algorithm used with this key
    
    # Key state and lifecycle
    state: QKDKeyState = QKDKeyState.READY
    is_consumed: bool = False
    consumed_by: Optional[str] = None  # User ID who consumed the key
    consumed_at: Optional[datetime] = None
    reserved_by: Optional[str] = None  # User ID who reserved the key
    reserved_at: Optional[datetime] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    last_accessed_at: Optional[datetime] = None
    
    # Entropy and quality metrics
    entropy_score: float = 1.0  # Shannon entropy score (0-1)
    quality_score: float = 1.0  # Overall quality score (0-1)
    quantum_grade: bool = True  # Whether key meets quantum-grade standards
    
    # Audit trail
    operation_history: Optional[List[Dict[str, Any]]] = None  # List of operations
    
    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}
        use_enum_values = True


class QKDSessionDocument(BaseModel):
    """
    QKD Session document for MongoDB.
    Tracks quantum key distribution sessions between two parties.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    
    # Session identifiers
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    flow_id: Optional[str] = None  # Associated encryption flow
    
    # Participants
    sender_email: str
    sender_sae_id: Optional[str] = None  # Sender's SAE ID
    receiver_email: str
    receiver_sae_id: Optional[str] = None  # Receiver's SAE ID
    
    # KME information
    kme1_endpoint: Optional[str] = None  # KME1 server endpoint
    kme2_endpoint: Optional[str] = None  # KME2 server endpoint
    
    # Keys used in session
    key_ids: List[str] = Field(default_factory=list)
    total_keys_used: int = 0
    total_bits_exchanged: int = 0
    
    # Session state
    is_active: bool = True
    is_successful: bool = False
    error_message: Optional[str] = None
    
    # Security metrics
    security_level: int = 1
    encryption_algorithm: Optional[str] = None
    
    # Timestamps
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class QKDAuditLogDocument(BaseModel):
    """
    QKD Audit Log document for MongoDB.
    Tracks all QKD-related operations for security auditing.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    
    # Operation details
    operation: str  # e.g., "KEY_GENERATED", "KEY_CONSUMED", "KEY_EXPIRED"
    key_id: Optional[str] = None
    session_id: Optional[str] = None
    flow_id: Optional[str] = None
    
    # Actor information
    user_email: Optional[str] = None
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    # Operation result
    success: bool = True
    error_message: Optional[str] = None
    
    # Details
    details: Optional[Dict[str, Any]] = None
    
    # Timestamp
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Security classification
    severity: str = "INFO"  # INFO, WARNING, ERROR, CRITICAL
    
    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class QKDKeyPoolStatusDocument(BaseModel):
    """
    QKD Key Pool Status document for MongoDB.
    Tracks the status of the quantum key pool for monitoring.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    
    # Pool identification
    kme_id: str  # KME1 or KME2
    sae_id: Optional[str] = None
    
    # Key counts
    total_keys: int = 0
    available_keys: int = 0
    reserved_keys: int = 0
    consumed_keys: int = 0
    expired_keys: int = 0
    
    # Capacity metrics
    pool_capacity: int = 1000
    utilization_percent: float = 0.0
    
    # Last activity
    last_key_generated: Optional[datetime] = None
    last_key_consumed: Optional[datetime] = None
    
    # Health status
    is_healthy: bool = True
    last_health_check: datetime = Field(default_factory=datetime.utcnow)
    error_count: int = 0
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}

