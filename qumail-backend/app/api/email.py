from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from ..schemas.email_schema import EmailCreateRequest, EmailListResponse, EmailDetail, SendEmailResponse
from datetime import datetime, timedelta
import uuid

router = APIRouter(prefix="/api/v1/emails", tags=["emails"])

# Mock data for testing
MOCK_EMAILS = [
    {
        "id": str(uuid.uuid4()),
        "flow_id": f"flow-{uuid.uuid4()}",
        "sender_email": "alice@quantummail.com",
        "receiver_email": "user@example.com",
        "subject": "Quantum Key Distribution Report",
        "security_level": 1,  # Quantum One-Time Pad
        "direction": "RECEIVED",
        "timestamp": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
        "is_read": False,
        "is_starred": True,
        "is_suspicious": False,
        "body": "Here's the latest quantum key distribution report. Our entropy rate is excellent!",
        "snippet": "Here's the latest quantum key distribution report...",
        "attachments": [
            {
                "filename": "qkd_report.pdf",
                "size": 2456233,
                "content_type": "application/pdf"
            }
        ]
    },
    {
        "id": str(uuid.uuid4()),
        "flow_id": f"flow-{uuid.uuid4()}",
        "sender_email": "bob@quantummail.com",
        "receiver_email": "user@example.com",
        "subject": "KME Server Status Update",
        "security_level": 2,  # Quantum-Enhanced AES
        "direction": "RECEIVED",
        "timestamp": (datetime.utcnow() - timedelta(hours=3)).isoformat(),
        "is_read": True,
        "is_starred": False,
        "is_suspicious": False,
        "body": "The KME servers are operating at optimal capacity. We've added more quantum random number generators to improve entropy.",
        "snippet": "The KME servers are operating at optimal capacity...",
        "attachments": []
    },
    {
        "id": str(uuid.uuid4()),
        "flow_id": f"flow-{uuid.uuid4()}",
        "sender_email": "user@example.com",
        "receiver_email": "charlie@quantummail.com",
        "subject": "Re: Encryption Protocol Update",
        "security_level": 1,  # Quantum One-Time Pad
        "direction": "SENT",
        "timestamp": (datetime.utcnow() - timedelta(hours=5)).isoformat(),
        "is_read": True,
        "is_starred": False,
        "is_suspicious": False,
        "body": "I've reviewed the new quantum encryption protocol. The key refresh rate looks good, but we should increase the authentication strength.",
        "snippet": "I've reviewed the new quantum encryption protocol...",
        "attachments": []
    },
    {
        "id": str(uuid.uuid4()),
        "flow_id": f"flow-{uuid.uuid4()}",
        "sender_email": "eve@suspicious.com",
        "receiver_email": "user@example.com",
        "subject": "Security Vulnerability",
        "security_level": 4,  # Standard RSA
        "direction": "RECEIVED",
        "timestamp": (datetime.utcnow() - timedelta(hours=6)).isoformat(),
        "is_read": False,
        "is_starred": False,
        "is_suspicious": True,
        "body": "We've detected a security issue with your account. Please click the link below to verify your information.",
        "snippet": "We've detected a security issue with your account...",
        "attachments": [
            {
                "filename": "security_patch.exe",
                "size": 1345622,
                "content_type": "application/octet-stream"
            }
        ]
    },
    {
        "id": str(uuid.uuid4()),
        "flow_id": f"flow-{uuid.uuid4()}",
        "sender_email": "david@quantummail.com",
        "receiver_email": "user@example.com",
        "subject": "Quantum Entropy Source Test Results",
        "security_level": 3,  # Post-Quantum
        "direction": "RECEIVED",
        "timestamp": (datetime.utcnow() - timedelta(days=1)).isoformat(),
        "is_read": True,
        "is_starred": True,
        "is_suspicious": False,
        "body": "The test results for our new quantum entropy source look promising. We're seeing a 23% increase in randomness quality.",
        "snippet": "The test results for our new quantum entropy source...",
        "attachments": [
            {
                "filename": "entropy_results.xlsx",
                "size": 456789,
                "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            }
        ]
    }
]

@router.get("", response_model=EmailListResponse)
async def list_emails(
    folder: str = "inbox",
    security_level: Optional[int] = None,
    search_query: Optional[str] = None,
    is_read: Optional[bool] = None,
    has_attachments: Optional[bool] = None,
):
    # Filter emails based on folder
    if folder == "inbox":
        emails = [e for e in MOCK_EMAILS if e["direction"] == "RECEIVED"]
    elif folder == "sent":
        emails = [e for e in MOCK_EMAILS if e["direction"] == "SENT"]
    elif folder == "starred":
        emails = [e for e in MOCK_EMAILS if e["is_starred"]]
    else:
        emails = MOCK_EMAILS
        
    # Apply filters
    if security_level is not None:
        emails = [e for e in emails if e["security_level"] == security_level]
    
    if search_query:
        search_query = search_query.lower()
        emails = [e for e in emails if 
                  search_query in e["subject"].lower() or 
                  search_query in e["sender_email"].lower() or 
                  search_query in e["body"].lower()]
    
    if is_read is not None:
        emails = [e for e in emails if e["is_read"] == is_read]
        
    if has_attachments is not None:
        emails = [e for e in emails if bool(e["attachments"]) == has_attachments]
        
    return EmailListResponse(
        emails=emails,
        total=len(emails),
        next_page_token=None
    )

@router.get("/{email_id}", response_model=EmailDetail)
async def get_email(email_id: str):
    # Find the email by ID
    email = next((e for e in MOCK_EMAILS if e["id"] == email_id), None)
    
    if not email:
        # If not found by direct ID match, return the first email (for demo purposes)
        email = MOCK_EMAILS[0]
        email["id"] = email_id  # Set the requested ID
        
    return EmailDetail(**email)

@router.post("/send", response_model=SendEmailResponse)
async def send_email(payload: EmailCreateRequest):
    # Create a mock response for sending
    return SendEmailResponse(
        flow_id=f"flow-{uuid.uuid4()}", 
        gmail_message_id=f"msg-{uuid.uuid4()}", 
        security_level=payload.security_level
    )
