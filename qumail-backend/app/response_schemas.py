from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime

class AuthURLResponse(BaseModel):
    """Response model for OAuth authorization URL"""
    authorization_url: str
    state: str
    message: str

class OAuthCallbackResponse(BaseModel):
    """Response model for OAuth callback"""
    success: bool
    user_email: str
    display_name: str
    session_token: str
    expires_at: str
    message: str

class MessageSummary(BaseModel):
    """Summary of a Gmail message"""
    id: str
    thread_id: str
    subject: str
    from_address: str = Field(alias="from")
    date: str
    snippet: str
    labels: List[str]
    security_level: str
    has_attachments: bool

class MessageListResponse(BaseModel):
    """Response model for message list"""
    messages: List[MessageSummary]
    next_page_token: Optional[str]
    result_size_estimate: int
    total_messages: int

class MessageDetailResponse(BaseModel):
    """Response model for detailed message"""
    id: str
    thread_id: str
    subject: str
    from_address: str = Field(alias="from")
    to: str
    cc: Optional[str]
    date: str
    body_text: str
    body_html: str
    security_level: str
    has_attachments: bool
    labels: List[str]
    raw_size: int
    raw_headers: Dict[str, str]

class SendEmailResponse(BaseModel):
    """Response model for sending email"""
    message_id: str
    thread_id: Optional[str]
    security_level: str
    encryption_applied: bool
    success: bool
    message: str

class UserInfoResponse(BaseModel):
    """Response model for user information"""
    user_id: str
    email: str
    display_name: str
    last_login: Optional[str]
    created_at: str
    oauth_connected: bool
    token_expires_at: Optional[str]

class EncryptionResponse(BaseModel):
    """Response model for encryption operations"""
    encrypted_content: str
    security_level: str
    encryption_algorithm: str
    signature: str
    metadata: Dict[str, Any]
    success: bool

class DecryptionResponse(BaseModel):
    """Response model for decryption operations"""
    decrypted_content: str
    security_level: str
    signature_valid: bool
    tampering_detected: bool
    success: bool
    message: str

class KMStatusResponse(BaseModel):
    """Response model for KM server status"""
    kme1_status: str
    kme2_status: str
    kme1_available_keys: int
    kme2_available_keys: int
    last_check: str
    connection_healthy: bool

class SecurityIncidentResponse(BaseModel):
    """Response model for security incidents"""
    id: str
    incident_type: str
    description: str
    severity: str
    user_id: Optional[str]
    timestamp: str
    details: Dict[str, Any]
    resolved: bool

class SecurityAuditResponse(BaseModel):
    """Response model for security audit log"""
    incidents: List[SecurityIncidentResponse]
    total_count: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    date_range: str

class SystemStatusResponse(BaseModel):
    """Response model for system status"""
    status: str
    version: str
    uptime: str
    km_servers: KMStatusResponse
    database_healthy: bool
    oauth_configured: bool
    security_auditor_active: bool
    last_health_check: str

class ErrorResponse(BaseModel):
    """Standard error response model"""
    error: str
    detail: str
    error_code: Optional[str]
    timestamp: str
    request_id: Optional[str]

# Security specific responses

class QuantumKeyResponse(BaseModel):
    """Response model for quantum key operations"""
    key_available: bool
    key_id: Optional[str]
    key_size: Optional[int]
    source_km: str
    consumed: bool
    security_parameters: Dict[str, Any]

class CertificateValidationResponse(BaseModel):
    """Response model for certificate validation"""
    valid: bool
    serial_number: str
    subject: str
    issuer: str
    expires_at: str
    validation_details: Dict[str, Any]

class SecurityLevelValidationResponse(BaseModel):
    """Response model for security level validation"""
    requested_level: str
    applied_level: str
    security_features: List[str]
    encryption_algorithm: str
    key_sources: List[str]
    signature_algorithm: str
    additional_protections: List[str]

# API Health and Status responses

class HealthCheckResponse(BaseModel):
    """Response model for health checks"""
    healthy: bool
    services: Dict[str, str]  # service_name -> status
    version: str
    timestamp: str
    uptime_seconds: float

class MetricsResponse(BaseModel):
    """Response model for system metrics"""
    total_emails_sent: int
    emails_by_security_level: Dict[str, int]
    security_incidents: Dict[str, int]
    oauth_sessions: int
    km_key_consumption: Dict[str, int]
    last_24h_activity: Dict[str, int]
    system_load: Dict[str, float]

# Utility response types

class SuccessResponse(BaseModel):
    """Generic success response"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

class ValidationResponse(BaseModel):
    """Response model for validation operations"""
    valid: bool
    errors: List[str]
    warnings: List[str]
    details: Optional[Dict[str, Any]]