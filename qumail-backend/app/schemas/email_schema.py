from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from typing import List, Optional, Dict, Any, Union

class EmailCreateRequest(BaseModel):
    to: EmailStr
    subject: str
    body: str
    security_level: int = Field(ge=1, le=4)
    attachments: List[str] = []  # placeholder for attachment identifiers

class AttachmentSchema(BaseModel):
    filename: str
    size: int
    content_type: str

class EmailMetadata(BaseModel):
    id: str
    flow_id: str
    sender_email: str  # Changed from EmailStr to str for mock data
    receiver_email: str  # Changed from EmailStr to str for mock data
    subject: str
    security_level: int
    direction: str
    timestamp: str  # Changed from datetime to str to handle ISO format
    is_read: bool
    is_starred: bool
    is_suspicious: bool
    snippet: Optional[str] = None
    attachments: List[Dict[str, Any]] = []
    
    # Convert string timestamp to datetime if needed
    @field_validator('timestamp', mode='before')
    @classmethod
    def parse_timestamp(cls, v):
        if isinstance(v, datetime):
            return v.isoformat()
        return v

class EmailDetail(EmailMetadata):
    body: str
    attachments: List[Dict[str, Any]] = []

class EmailListResponse(BaseModel):
    emails: List[EmailMetadata]
    total: int = 0
    next_page_token: Optional[str] = None

class SendEmailResponse(BaseModel):
    flow_id: str
    gmail_message_id: Optional[str] = None
    security_level: int
