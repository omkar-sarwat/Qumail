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
