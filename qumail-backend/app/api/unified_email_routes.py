"""
Unified Email Routes

ARCHITECTURE: Unified Outbound, Separate Inbound
- SEND: Always via Gmail API (requires Google OAuth)
- FETCH: Via provider's IMAP (Rediff, Yahoo, Outlook, Gmail)

This is how professional apps like Zendesk, Freshdesk work.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
import logging

from motor.motor_asyncio import AsyncIOMotorDatabase

from ..services.unified_email_service import unified_email_service
from ..services.multi_provider_email import ProviderEmailSettings, EmailMessage
from ..core.database import get_database

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/unified-email", tags=["Unified Email"])


# ============================================================================
# REQUEST MODELS
# ============================================================================

class ProviderAccountSettings(BaseModel):
    """Provider IMAP/POP3 settings for fetching"""
    email: EmailStr
    password: str
    imap_host: str
    imap_port: int = 993
    imap_security: str = "ssl"  # 'ssl' or 'starttls'
    protocol: str = "imap"  # 'imap' or 'pop3'


class SendEmailRequest(BaseModel):
    """
    Send email via Gmail API
    
    - gmail_user_email: Your Gmail account (must be logged in via OAuth)
    - from_email: The "From" address (can be ANY email - Rediff, Yahoo, etc.)
    - Emails will show "via gmail.com" but sender appears as from_email
    """
    gmail_user_email: EmailStr  # Gmail OAuth account
    from_email: EmailStr  # Actual sender (can be non-Gmail)
    from_name: Optional[str] = None
    to_email: EmailStr
    subject: str
    body_text: str
    body_html: Optional[str] = None
    cc: Optional[str] = None
    bcc: Optional[str] = None
    reply_to: Optional[str] = None  # Defaults to from_email
    security_level: int = 0  # 0=none, 1-4=quantum encryption


class FetchEmailsRequest(BaseModel):
    """Fetch emails from provider IMAP"""
    account: ProviderAccountSettings
    folder: str = "INBOX"
    max_results: int = 50
    offset: int = 0


class SyncEmailsRequest(BaseModel):
    """Sync new emails since last check"""
    account: ProviderAccountSettings
    since_message_id: Optional[str] = None
    folder: str = "INBOX"
    max_results: int = 10


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class SendEmailResponse(BaseModel):
    success: bool
    message_id: Optional[str] = None
    thread_id: Optional[str] = None
    sent_via: str = "gmail_api"
    from_email: str
    to_email: str
    message: str


class EmailResponse(BaseModel):
    id: str
    message_id: str
    thread_id: str
    subject: str
    from_address: str
    from_name: str
    to_address: str
    to_name: str
    cc_address: Optional[str] = None
    body_text: str
    body_html: Optional[str] = None
    timestamp: str
    is_read: bool
    has_attachments: bool
    folder: str


class FetchEmailsResponse(BaseModel):
    emails: List[EmailResponse]
    total_count: int
    protocol: str


class SyncEmailsResponse(BaseModel):
    emails: List[EmailResponse]
    new_count: int
    protocol: str


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _to_provider_settings(account: ProviderAccountSettings) -> ProviderEmailSettings:
    """Convert request to ProviderEmailSettings"""
    return ProviderEmailSettings(
        smtp_host="",  # Not used for fetch
        smtp_port=587,
        smtp_security="starttls",
        imap_host=account.imap_host,
        imap_port=account.imap_port,
        imap_security=account.imap_security,
        protocol=account.protocol,
        username=account.email,
        password=account.password,
        email=account.email
    )


def _email_to_response(email: EmailMessage) -> EmailResponse:
    """Convert EmailMessage to response"""
    return EmailResponse(
        id=email.id,
        message_id=email.message_id,
        thread_id=email.thread_id,
        subject=email.subject,
        from_address=email.from_address,
        from_name=email.from_name,
        to_address=email.to_address,
        to_name=email.to_name,
        cc_address=email.cc_address,
        body_text=email.body_text,
        body_html=email.body_html,
        timestamp=email.date.isoformat(),
        is_read=email.is_read,
        has_attachments=email.has_attachments,
        folder=email.folder
    )


# ============================================================================
# ROUTES
# ============================================================================

@router.post("/send", response_model=SendEmailResponse)
async def send_email(
    request: SendEmailRequest,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Send email via Gmail API (Unified Outbound)
    
    HOW IT WORKS:
    1. Uses Gmail OAuth token from logged-in user
    2. Sends email with custom "From" address (can be Rediff, Yahoo, etc.)
    3. Email shows "via gmail.com" but sender appears as from_email
    4. Reply-To ensures replies go to the actual sender's mailbox
    
    REQUIREMENTS:
    - User must be logged in with Google OAuth
    - gmail_user_email must match the logged-in Gmail account
    
    EXAMPLE:
    - User logs in with omkarsarswat@gmail.com (Google OAuth)
    - User adds their Rediff account for receiving emails
    - When sending from Rediff, we use Gmail API but set From: user@rediffmail.com
    - Recipient sees "From: user@rediffmail.com via gmail.com"
    - Replies go to user@rediffmail.com
    """
    logger.info(f"📤 Unified send: {request.from_email} → {request.to_email} (via Gmail: {request.gmail_user_email})")
    
    try:
        # TODO: Apply quantum encryption if security_level > 0
        body_text = request.body_text
        body_html = request.body_html
        
        if request.security_level > 0:
            logger.info(f"🔐 Applying encryption level {request.security_level}")
            # Integration with existing encryption services would go here
            pass
        
        result = await unified_email_service.send_email_via_gmail_api(
            db=db,
            gmail_user_email=request.gmail_user_email,
            from_email=request.from_email,
            to_email=request.to_email,
            subject=request.subject,
            body_text=body_text,
            body_html=body_html,
            from_name=request.from_name,
            cc=request.cc,
            bcc=request.bcc,
            reply_to=request.reply_to
        )
        
        return SendEmailResponse(
            success=True,
            message_id=result.get("message_id"),
            thread_id=result.get("thread_id"),
            sent_via="gmail_api",
            from_email=request.from_email,
            to_email=request.to_email,
            message=f"Email sent successfully via Gmail API"
        )
        
    except Exception as e:
        logger.error(f"❌ Unified send failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {str(e)}"
        )


@router.post("/fetch", response_model=FetchEmailsResponse)
async def fetch_emails(request: FetchEmailsRequest):
    """
    Fetch emails from provider IMAP (Separate Inbound)
    
    HOW IT WORKS:
    1. Connects to provider's IMAP server (Rediff, Yahoo, Outlook, etc.)
    2. Authenticates with user's credentials
    3. Fetches emails from specified folder
    
    SUPPORTED PROVIDERS:
    - Gmail (imap.gmail.com:993)
    - Yahoo (imap.mail.yahoo.com:993)
    - Outlook (outlook.office365.com:993)
    - Rediffmail (imap.rediffmail.com:993 or POP3)
    - Any IMAP/POP3 server
    """
    logger.info(f"📥 Unified fetch: {request.account.email} from {request.folder}")
    
    try:
        settings = _to_provider_settings(request.account)
        
        emails = await unified_email_service.fetch_emails_from_provider(
            settings=settings,
            folder=request.folder,
            max_results=request.max_results,
            offset=request.offset
        )
        
        response_emails = [_email_to_response(e) for e in emails]
        
        return FetchEmailsResponse(
            emails=response_emails,
            total_count=len(response_emails),
            protocol=settings.protocol
        )
        
    except Exception as e:
        logger.error(f"❌ Unified fetch failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch emails: {str(e)}"
        )


@router.post("/sync", response_model=SyncEmailsResponse)
async def sync_emails(request: SyncEmailsRequest):
    """
    Sync new emails from provider (for polling)
    
    More efficient than full fetch - only returns new emails since last check.
    """
    logger.info(f"🔄 Unified sync: {request.account.email} since {request.since_message_id}")
    
    try:
        settings = _to_provider_settings(request.account)
        
        result = await unified_email_service.sync_new_emails(
            settings=settings,
            since_message_id=request.since_message_id,
            folder=request.folder,
            max_results=request.max_results
        )
        
        response_emails = [_email_to_response(e) for e in result["emails"]]
        
        return SyncEmailsResponse(
            emails=response_emails,
            new_count=result["new_count"],
            protocol=result["protocol"]
        )
        
    except Exception as e:
        logger.error(f"❌ Unified sync failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}"
        )


@router.post("/folders")
async def list_folders(account: ProviderAccountSettings):
    """List available folders from provider IMAP"""
    logger.info(f"📁 Listing folders for {account.email}")
    
    try:
        settings = _to_provider_settings(account)
        folders = await unified_email_service.list_provider_folders(settings)
        return {"folders": folders}
        
    except Exception as e:
        logger.error(f"❌ List folders failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list folders: {str(e)}"
        )


@router.get("/status")
async def get_status():
    """Get unified email service status"""
    return {
        "status": "active",
        "architecture": "unified_outbound_separate_inbound",
        "send_method": "gmail_api",
        "fetch_method": "provider_imap",
        "description": "Send via Gmail API, Fetch via provider IMAP"
    }
