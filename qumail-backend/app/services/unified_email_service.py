"""
Unified Email Service
- OUTBOUND: Always through Gmail API (using Google OAuth)
- INBOUND: Through provider's IMAP (Rediff, Yahoo, Outlook, Gmail)

This is the "Unified Outbound, Separate Inbound" pattern used by
Zendesk, Freshdesk, and other professional email apps.
"""

import base64
import logging
import aiohttp
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from .gmail_oauth import oauth_service
from .multi_provider_email import multi_provider_client, ProviderEmailSettings, EmailMessage

logger = logging.getLogger(__name__)

GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1"


@dataclass
class UnifiedSendRequest:
    """Request to send email via unified outbound"""
    gmail_user_email: str  # Gmail account for OAuth (the logged-in user)
    from_email: str  # Actual "From" address (can be Rediff, Yahoo, etc.)
    from_name: Optional[str]
    to_email: str
    subject: str
    body_text: str
    body_html: Optional[str] = None
    cc: Optional[str] = None
    bcc: Optional[str] = None
    reply_to: Optional[str] = None


class UnifiedEmailService:
    """
    Unified Email Service
    
    Send: Always via Gmail API (requires Google OAuth login)
    Fetch: Via provider's IMAP/POP3 (works for any provider)
    """
    
    async def send_email_via_gmail_api(
        self,
        db,  # AsyncIOMotorDatabase
        gmail_user_email: str,
        from_email: str,
        to_email: str,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
        from_name: Optional[str] = None,
        cc: Optional[str] = None,
        bcc: Optional[str] = None,
        reply_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send email using Gmail API with OAuth token.
        
        This allows sending emails with ANY "From" address while using
        Gmail's infrastructure. The email will show "via gmail.com" but
        this is acceptable for most use cases.
        
        Args:
            db: MongoDB database session
            gmail_user_email: The Gmail account to use for OAuth (logged-in user)
            from_email: The "From" address (can be any email, e.g., user@rediffmail.com)
            to_email: Recipient email address
            subject: Email subject
            body_text: Plain text body
            body_html: HTML body (optional)
            from_name: Display name for From header
            cc: CC recipients (comma-separated)
            bcc: BCC recipients (comma-separated)
            reply_to: Reply-To address (defaults to from_email)
        
        Returns:
            Dict with success status, messageId, threadId
        """
        try:
            # Get valid Gmail OAuth access token
            logger.info(f"📤 Sending via Gmail API (OAuth) | From: {from_email} | To: {to_email}")
            
            access_token = await oauth_service.get_valid_access_token(gmail_user_email, db)
            
            if not access_token:
                raise Exception(f"No valid OAuth token for {gmail_user_email}. User must login with Google first.")
            
            # Build MIME message
            if body_html:
                msg = MIMEMultipart('alternative')
                msg.attach(MIMEText(body_text, 'plain', 'utf-8'))
                msg.attach(MIMEText(body_html, 'html', 'utf-8'))
            else:
                msg = MIMEText(body_text, 'plain', 'utf-8')
            
            # Set headers
            if from_name:
                msg['From'] = f"{from_name} <{from_email}>"
            else:
                msg['From'] = from_email
            
            msg['To'] = to_email
            msg['Subject'] = subject
            
            if cc:
                msg['Cc'] = cc
            
            # Reply-To ensures replies go to the actual user's mailbox
            msg['Reply-To'] = reply_to or from_email
            
            # Add X-Original-Sender for transparency
            msg['X-Original-Sender'] = from_email
            
            # Encode as base64url
            raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')
            
            # Send via Gmail API
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            payload = {"raw": raw_message}
            
            async with aiohttp.ClientSession() as session:
                url = f"{GMAIL_API_BASE}/users/me/messages/send"
                
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 401:
                        # Token expired, try refresh
                        logger.info(f"Token expired for {gmail_user_email}, refreshing...")
                        access_token = await oauth_service.refresh_access_token(gmail_user_email, db)
                        headers["Authorization"] = f"Bearer {access_token}"
                        
                        async with session.post(url, headers=headers, json=payload) as retry_response:
                            if retry_response.status != 200:
                                error = await retry_response.text()
                                raise Exception(f"Gmail API error after refresh: {error}")
                            data = await retry_response.json()
                    elif response.status != 200:
                        error = await response.text()
                        raise Exception(f"Gmail API error: {error}")
                    else:
                        data = await response.json()
            
            message_id = data.get("id", "")
            thread_id = data.get("threadId", "")
            
            logger.info(f"✅ Email sent via Gmail API | MessageId: {message_id} | From: {from_email} → To: {to_email}")
            
            return {
                "success": True,
                "message_id": message_id,
                "thread_id": thread_id,
                "sent_via": "gmail_api",
                "from_email": from_email,
                "to_email": to_email
            }
            
        except Exception as e:
            logger.error(f"❌ Gmail API send failed: {e}")
            raise Exception(f"Failed to send email via Gmail API: {str(e)}")
    
    async def fetch_emails_from_provider(
        self,
        settings: ProviderEmailSettings,
        folder: str = "INBOX",
        max_results: int = 50,
        offset: int = 0
    ) -> List[EmailMessage]:
        """
        Fetch emails from any provider via IMAP or POP3.
        
        This uses the existing multi_provider_client for maximum compatibility.
        
        Args:
            settings: Provider connection settings (IMAP/POP3 credentials)
            folder: Folder to fetch from (INBOX, Sent, etc.)
            max_results: Maximum emails to fetch
            offset: Offset for pagination (IMAP only)
        
        Returns:
            List of EmailMessage objects
        """
        logger.info(f"📥 Fetching emails via {settings.protocol.upper()} from {settings.imap_host}")
        
        if settings.protocol == 'pop3':
            # POP3 is synchronous
            import asyncio
            loop = asyncio.get_event_loop()
            emails = await loop.run_in_executor(
                None,
                multi_provider_client.fetch_emails_pop3,
                settings,
                max_results
            )
        else:
            # IMAP is async
            emails = await multi_provider_client.fetch_emails_imap(
                settings,
                folder=folder,
                max_results=max_results,
                offset=offset
            )
        
        logger.info(f"✅ Fetched {len(emails)} emails from {settings.email or settings.username}")
        return emails
    
    async def fetch_gmail_emails(
        self,
        db,
        gmail_user_email: str,
        folder: str = "INBOX",
        max_results: int = 50,
        page_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fetch emails from Gmail using Gmail API (for Gmail users).
        
        This provides better performance for Gmail accounts.
        
        Args:
            db: MongoDB database session
            gmail_user_email: Gmail account email
            folder: Label/folder to fetch from
            max_results: Maximum results
            page_token: Pagination token
        
        Returns:
            Dict with emails and pagination info
        """
        from .gmail_service import gmail_service
        
        access_token = await oauth_service.get_valid_access_token(gmail_user_email, db)
        
        if not access_token:
            raise Exception(f"No valid OAuth token for {gmail_user_email}")
        
        return await gmail_service.fetch_emails(
            access_token=access_token,
            folder=folder,
            max_results=max_results,
            page_token=page_token
        )
    
    async def list_provider_folders(
        self,
        settings: ProviderEmailSettings
    ) -> List[str]:
        """List folders from provider via IMAP"""
        if settings.protocol == 'pop3':
            return ["INBOX"]  # POP3 only has inbox
        
        return await multi_provider_client.list_folders_imap(settings)
    
    async def sync_new_emails(
        self,
        settings: ProviderEmailSettings,
        since_message_id: Optional[str] = None,
        folder: str = "INBOX",
        max_results: int = 10
    ) -> Dict[str, Any]:
        """
        Sync new emails from provider since last message ID.
        
        Args:
            settings: Provider settings
            since_message_id: Last known message ID
            folder: Folder to sync
            max_results: Max new emails to fetch
        
        Returns:
            Dict with new emails and count
        """
        if settings.protocol == 'pop3':
            # POP3 doesn't support efficient sync
            import asyncio
            loop = asyncio.get_event_loop()
            emails = await loop.run_in_executor(
                None,
                multi_provider_client.fetch_emails_pop3,
                settings,
                max_results
            )
            return {
                "emails": emails,
                "new_count": len(emails),
                "protocol": "pop3"
            }
        else:
            new_emails, new_count = await multi_provider_client.fetch_new_emails_since(
                settings,
                since_message_id=since_message_id,
                folder=folder,
                max_results=max_results
            )
            return {
                "emails": new_emails,
                "new_count": new_count,
                "protocol": "imap"
            }


# Singleton instance
unified_email_service = UnifiedEmailService()
