"""
Multi-provider email routes
Supports any email provider via IMAP/POP3/SMTP
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
import logging
import asyncio
from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorDatabase

from ..services.multi_provider_email import (
    multi_provider_client,
    ProviderEmailSettings,
    EmailMessage
)
from ..services.provider_registry import detect_provider
from ..services.gmail_oauth import oauth_service
from ..core.database import get_database

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/provider-email", tags=["Multi-Provider Email"])


class AccountSettingsRequest(BaseModel):
    """Account settings from frontend"""
    email: EmailStr
    password: str
    smtp_host: str
    smtp_port: int
    smtp_security: str  # 'ssl' or 'starttls'
    imap_host: str
    imap_port: int
    imap_security: str  # 'ssl' or 'starttls'
    protocol: str  # 'imap' or 'pop3'


class FetchEmailsRequest(BaseModel):
    """Request to fetch emails"""
    account: AccountSettingsRequest
    folder: str = "INBOX"
    max_results: int = 50
    offset: int = 0


class SendEmailRequest(BaseModel):
    """Request to send email"""
    account: AccountSettingsRequest
    to_address: str
    subject: str
    body_text: str
    body_html: Optional[str] = None
    cc_address: Optional[str] = None
    bcc_address: Optional[str] = None
    security_level: int = 0  # 0 = no encryption, 1-4 = quantum encryption levels
    use_gmail_oauth: bool = False  # When true, send via Gmail SMTP XOAUTH2
    gmail_email: Optional[EmailStr] = None  # Gmail account to send through


class EmailResponse(BaseModel):
    """Email response"""
    id: str
    message_id: str
    thread_id: str
    subject: str
    from_address: str
    from_name: str
    to_address: str
    to_name: str
    cc_address: Optional[str]
    body_text: str
    body_html: Optional[str]
    timestamp: str
    is_read: bool
    has_attachments: bool
    folder: str


class EmailListResponse(BaseModel):
    """Email list response"""
    emails: List[EmailResponse]
    total_count: int


class SendEmailResponse(BaseModel):
    """Send email response"""
    success: bool
    message_id: Optional[str]
    message: str


class TestConnectionResponse(BaseModel):
    """Test connection response"""
    success: bool
    protocol: str
    message: str
    details: Dict[str, Any]


def _convert_to_provider_settings(account: AccountSettingsRequest) -> ProviderEmailSettings:
    """Convert request to provider settings"""
    return ProviderEmailSettings(
        smtp_host=account.smtp_host,
        smtp_port=account.smtp_port,
        smtp_security=account.smtp_security,
        imap_host=account.imap_host,
        imap_port=account.imap_port,
        imap_security=account.imap_security,
        protocol=account.protocol,
        username=account.email,  # Use email as login username
        password=account.password,
        email=account.email,  # User's actual email for From/Reply-To
    )


def _email_to_response(email_msg: EmailMessage) -> EmailResponse:
    """Convert EmailMessage to response"""
    return EmailResponse(
        id=email_msg.id,
        message_id=email_msg.message_id,
        thread_id=email_msg.thread_id,
        subject=email_msg.subject,
        from_address=email_msg.from_address,
        from_name=email_msg.from_name,
        to_address=email_msg.to_address,
        to_name=email_msg.to_name,
        cc_address=email_msg.cc_address,
        body_text=email_msg.body_text,
        body_html=email_msg.body_html,
        timestamp=email_msg.date.isoformat(),
        is_read=email_msg.is_read,
        has_attachments=email_msg.has_attachments,
        folder=email_msg.folder
    )


@router.post("/test-connection", response_model=TestConnectionResponse)
async def test_connection(account: AccountSettingsRequest):
    """
    Test connection to email provider (IMAP or POP3)
    
    Use this before adding an account to verify credentials work.
    """
    logger.info(f"🔌 Testing connection for {account.email} via {account.protocol}")
    logger.info(f"   Host: {account.imap_host}:{account.imap_port} ({account.imap_security})")
    
    settings = _convert_to_provider_settings(account)
    
    try:
        if settings.protocol == 'pop3':
            # Test POP3 connection
            import ssl
            import poplib
            
            context = ssl.create_default_context()
            
            if settings.imap_security == 'ssl':
                pop = poplib.POP3_SSL(
                    settings.imap_host,
                    settings.imap_port,
                    context=context,
                    timeout=30
                )
            else:
                pop = poplib.POP3(
                    settings.imap_host,
                    settings.imap_port,
                    timeout=30
                )
                if settings.imap_security == 'starttls':
                    pop.stls(context=context)
            
            # Login
            pop.user(settings.username)
            pop.pass_(settings.password)
            
            # Get message count
            num_messages = len(pop.list()[1])
            
            pop.quit()
            
            return TestConnectionResponse(
                success=True,
                protocol="pop3",
                message=f"Successfully connected to POP3. Found {num_messages} messages.",
                details={
                    "host": settings.imap_host,
                    "port": settings.imap_port,
                    "security": settings.imap_security,
                    "message_count": num_messages
                }
            )
        else:
            # Test IMAP connection
            client = await multi_provider_client.connect_imap(settings)
            
            # List folders
            _, folder_data = await client.list('', '*')
            folder_count = len(folder_data) if folder_data else 0
            
            # Get inbox count
            await client.select('INBOX')
            _, data = await client.search('ALL')
            message_count = len(data[0].split()) if data and data[0] else 0
            
            return TestConnectionResponse(
                success=True,
                protocol="imap",
                message=f"Successfully connected to IMAP. Found {message_count} messages in INBOX.",
                details={
                    "host": settings.imap_host,
                    "port": settings.imap_port,
                    "security": settings.imap_security,
                    "folder_count": folder_count,
                    "inbox_message_count": message_count
                }
            )
            
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Connection test failed for {account.email}: {error_msg}")
        
        # Provide helpful error messages
        if "authentication" in error_msg.lower() or "login" in error_msg.lower():
            hint = "Check username/password. For Gmail/Yahoo, use App Password."
        elif "timeout" in error_msg.lower():
            hint = "Connection timed out. Check host/port settings."
        elif "connection refused" in error_msg.lower():
            hint = "Connection refused. Check host and port are correct."
        elif "ssl" in error_msg.lower() or "tls" in error_msg.lower():
            hint = "SSL/TLS error. Try changing security setting."
        else:
            hint = "Check your email provider settings."
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Connection failed: {error_msg}. Hint: {hint}"
        )


@router.post("/fetch", response_model=EmailListResponse)
async def fetch_emails(request: FetchEmailsRequest):
    """
    Fetch emails from any provider via IMAP or POP3
    
    - Uses IMAP for providers that support it (Gmail, Yahoo, Outlook, etc.)
    - Falls back to POP3 for providers like Rediffmail
    """
    logger.info(f"📥 Fetching emails for {request.account.email} from {request.folder}")
    
    try:
        settings = _convert_to_provider_settings(request.account)
        
        if settings.protocol == 'pop3':
            # POP3 is synchronous, run in thread pool
            loop = asyncio.get_event_loop()
            emails = await loop.run_in_executor(
                None,
                multi_provider_client.fetch_emails_pop3,
                settings,
                request.max_results
            )
        else:
            # IMAP is async
            emails = await multi_provider_client.fetch_emails_imap(
                settings,
                folder=request.folder,
                max_results=request.max_results,
                offset=request.offset
            )
        
        response_emails = [_email_to_response(e) for e in emails]
        
        logger.info(f"✅ Fetched {len(response_emails)} emails for {request.account.email}")
        
        return EmailListResponse(
            emails=response_emails,
            total_count=len(response_emails)
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to fetch emails: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch emails: {str(e)}"
        )


@router.post("/send", response_model=SendEmailResponse)
async def send_email(
    request: SendEmailRequest,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Send email via SMTP
    
    Optionally encrypt with quantum encryption (levels 1-4)
    """
    logger.info(f"📤 Sending email from {request.account.email} to {request.to_address}")
    
    try:
        settings = _convert_to_provider_settings(request.account)
        
        body_text = request.body_text
        body_html = request.body_html
        
        # TODO: Apply quantum encryption if security_level > 0
        if request.security_level > 0:
            logger.info(f"🔐 Applying encryption level {request.security_level}")
            # Import encryption service and encrypt body
            # This would integrate with the existing encryption services
            pass
        
        oauth_access_token: Optional[str] = None
        oauth_user_email: Optional[str] = None

        if request.use_gmail_oauth:
            gmail_email = request.gmail_email or request.account.email
            oauth_user_email = gmail_email
            try:
                oauth_access_token = await oauth_service.get_valid_access_token(gmail_email, db)
                logger.info(f"✅ Gmail OAuth token acquired for {gmail_email}")
            except Exception as token_err:
                logger.error(f"❌ Gmail OAuth token fetch failed for {gmail_email}: {token_err}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Gmail OAuth token error: {token_err}"
                )

        result = await multi_provider_client.send_email_smtp(
            settings,
            to_address=request.to_address,
            subject=request.subject,
            body_text=body_text,
            body_html=body_html,
            cc_address=request.cc_address,
            bcc_address=request.bcc_address,
            oauth_user_email=oauth_user_email,
            oauth_access_token=oauth_access_token
        )
        
        logger.info(f"✅ Email sent successfully from {request.account.email}")
        
        return SendEmailResponse(
            success=True,
            message_id=result.get('message_id'),
            message=f"Email sent to {request.to_address}"
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to send email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {str(e)}"
        )


@router.post("/folders")
async def list_folders(account: AccountSettingsRequest):
    """
    List available folders via IMAP
    
    Note: POP3 doesn't support folders
    """
    logger.info(f"📁 Listing folders for {account.email}")
    
    try:
        settings = _convert_to_provider_settings(account)
        
        if settings.protocol == 'pop3':
            # POP3 only has INBOX
            return {"folders": ["INBOX"]}
        
        folders = await multi_provider_client.list_folders_imap(settings)
        
        return {"folders": folders}
        
    except Exception as e:
        logger.error(f"❌ Failed to list folders: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list folders: {str(e)}"
        )


class MarkReadRequest(BaseModel):
    account: AccountSettingsRequest
    message_id: str
    folder: str = "INBOX"


@router.post("/mark-read")
async def mark_as_read(request: MarkReadRequest):
    """Mark email as read via IMAP"""
    try:
        settings = _convert_to_provider_settings(request.account)
        
        if settings.protocol == 'pop3':
            # POP3 doesn't support read status
            return {"success": True, "message": "POP3 doesn't track read status"}
        
        await multi_provider_client.mark_as_read_imap(
            settings,
            request.message_id,
            request.folder
        )
        
        return {"success": True}
        
    except Exception as e:
        logger.error(f"❌ Failed to mark as read: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark as read: {str(e)}"
        )


class DeleteEmailRequest(BaseModel):
    account: AccountSettingsRequest
    message_id: str
    folder: str = "INBOX"


class SyncEmailsRequest(BaseModel):
    """Request to sync new emails since last check"""
    account: AccountSettingsRequest
    since_message_id: Optional[str] = None
    folder: str = "INBOX"
    max_results: int = 10


@router.post("/sync")
async def sync_emails(request: SyncEmailsRequest):
    """
    Sync new emails since last message ID.
    
    More efficient than full fetch - only returns emails newer than since_message_id.
    Used for continuous polling.
    """
    logger.info(f"🔄 Syncing emails for {request.account.email} since {request.since_message_id}")
    
    try:
        settings = _convert_to_provider_settings(request.account)
        
        if settings.protocol == 'pop3':
            # POP3 doesn't support efficient sync, do full fetch
            loop = asyncio.get_event_loop()
            emails = await loop.run_in_executor(
                None,
                multi_provider_client.fetch_emails_pop3,
                settings,
                request.max_results
            )
            
            # Filter out already-seen emails client-side
            response_emails = [_email_to_response(e) for e in emails]
            
            return {
                "emails": response_emails,
                "new_count": len(response_emails),
                "protocol": "pop3"
            }
        else:
            # IMAP supports efficient sync
            new_emails, new_count = await multi_provider_client.fetch_new_emails_since(
                settings,
                since_message_id=request.since_message_id,
                folder=request.folder,
                max_results=request.max_results
            )
            
            response_emails = [_email_to_response(e) for e in new_emails]
            
            logger.info(f"✅ Sync found {new_count} new emails for {request.account.email}")
            
            return {
                "emails": response_emails,
                "new_count": new_count,
                "protocol": "imap"
            }
        
    except Exception as e:
        logger.error(f"❌ Sync failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}"
        )


@router.post("/delete")
async def delete_email(request: DeleteEmailRequest):
    """Delete email via IMAP"""
    try:
        settings = _convert_to_provider_settings(request.account)
        
        if settings.protocol == 'pop3':
            return {"success": False, "message": "POP3 delete not implemented"}
        
        await multi_provider_client.delete_email_imap(
            settings,
            request.message_id,
            request.folder
        )
        
        return {"success": True}
        
    except Exception as e:
        logger.error(f"❌ Failed to delete email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete email: {str(e)}"
        )


@router.get("/auto-detect/{email}")
async def auto_detect_provider(email: str):
    """
    Auto-detect provider settings from email address
    
    Returns preset settings if provider is known, or manual mode if unknown
    """
    result = detect_provider(email)
    
    return {
        "email": email,
        "provider": result["provider"],
        "mode": result["mode"],
        "settings": result.get("settings")
    }
