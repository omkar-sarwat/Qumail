from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
from .schemas import SecurityLevel

class SendEmailRequest(BaseModel):
    """Request model for sending secure emails"""
    session_token: str = Field(..., description="Valid session token")
    to_addresses: List[EmailStr] = Field(..., min_items=1, description="List of recipient email addresses")
    subject: str = Field(..., max_length=998, description="Email subject line")
    body: str = Field(..., description="Email body content (plain text or HTML)")
    security_level: str = Field(default="LEVEL_1", description="Security level (LEVEL_1, LEVEL_2, LEVEL_3, LEVEL_4)")
    cc_addresses: Optional[List[EmailStr]] = Field(None, description="CC recipients")
    bcc_addresses: Optional[List[EmailStr]] = Field(None, description="BCC recipients")
    attachments: Optional[List[Dict[str, Any]]] = Field(None, description="Email attachments")

class GetMessagesRequest(BaseModel):
    """Request model for getting Gmail messages"""
    session_token: str = Field(..., description="Valid session token")
    query: Optional[str] = Field("", description="Gmail search query")
    max_results: int = Field(50, ge=1, le=500, description="Maximum number of messages to return")
    page_token: Optional[str] = Field(None, description="Pagination token for next page")

class MessageActionRequest(BaseModel):
    """Request model for message actions (modify labels, etc.)"""
    session_token: str = Field(..., description="Valid session token")
    add_label_ids: Optional[List[str]] = Field(None, description="Labels to add")
    remove_label_ids: Optional[List[str]] = Field(None, description="Labels to remove")

class EncryptionRequest(BaseModel):
    """Request model for encryption operations"""
    content: str = Field(..., description="Content to encrypt")
    security_level: str = Field(..., description="Security level for encryption")
    user_email: str = Field(..., description="User email for key derivation")

class DecryptionRequest(BaseModel):
    """Request model for decryption operations"""
    encrypted_content: str = Field(..., description="Encrypted content to decrypt")
    security_level: str = Field(..., description="Security level used for encryption")
    user_email: str = Field(..., description="User email for key derivation")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Encryption metadata")

class KMStatusRequest(BaseModel):
    """Request model for KM server status check"""
    user_email: str = Field(..., description="User email for authentication")
    target_km: Optional[str] = Field(None, description="Target KM server (kme1 or kme2)")

class SecurityAuditRequest(BaseModel):
    """Request model for security audit operations"""
    session_token: str = Field(..., description="Valid session token")
    incident_type: Optional[str] = Field(None, description="Filter by incident type")
    start_date: Optional[str] = Field(None, description="Start date for audit log (ISO format)")
    end_date: Optional[str] = Field(None, description="End date for audit log (ISO format)")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of audit records")