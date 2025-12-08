"""
Multi-provider email client service
Supports IMAP/POP3/SMTP for any email provider
"""

import asyncio
import email
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.header import decode_header
from email.utils import parseaddr
from typing import List, Dict, Any, Optional, Tuple
import os
import logging
import ssl
import poplib
from datetime import datetime
from dataclasses import dataclass

# IMAP support
import aioimaplib
import aiosmtplib

logger = logging.getLogger(__name__)


@dataclass
class ProviderEmailSettings:
    """Email provider connection settings"""
    smtp_host: str
    smtp_port: int
    smtp_security: str  # 'ssl' or 'starttls'
    imap_host: str
    imap_port: int
    imap_security: str  # 'ssl' or 'starttls'
    protocol: str  # 'imap' or 'pop3'
    username: str  # Login username (may differ from email)
    password: str
    email: str = ""  # User's actual email address (for From/Reply-To)
    
    def __post_init__(self):
        # If email not provided, use username as email
        if not self.email:
            self.email = self.username


@dataclass
class EmailMessage:
    """Represents an email message"""
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
    date: datetime
    is_read: bool
    has_attachments: bool
    folder: str
    raw_email: Optional[bytes] = None


class MultiProviderEmailClient:
    """
    Email client that works with any provider via IMAP/POP3/SMTP
    """
    
    def __init__(self):
        self._imap_connections: Dict[str, aioimaplib.IMAP4_SSL] = {}
        
    def _decode_header_value(self, header_value: str) -> str:
        """Decode email header value"""
        if not header_value:
            return ""
        decoded_parts = []
        for part, encoding in decode_header(header_value):
            if isinstance(part, bytes):
                try:
                    decoded_parts.append(part.decode(encoding or 'utf-8', errors='replace'))
                except:
                    decoded_parts.append(part.decode('utf-8', errors='replace'))
            else:
                decoded_parts.append(part)
        return ' '.join(decoded_parts)
    
    def _extract_email_body(self, msg: email.message.Message) -> Tuple[str, Optional[str]]:
        """Extract text and HTML body from email message"""
        body_text = ""
        body_html = None
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))
                
                # Skip attachments
                if "attachment" in content_disposition:
                    continue
                    
                if content_type == "text/plain":
                    try:
                        charset = part.get_content_charset() or 'utf-8'
                        payload = part.get_payload(decode=True)
                        if payload:
                            body_text = payload.decode(charset, errors='replace')
                    except Exception as e:
                        logger.warning(f"Failed to decode text body: {e}")
                        
                elif content_type == "text/html":
                    try:
                        charset = part.get_content_charset() or 'utf-8'
                        payload = part.get_payload(decode=True)
                        if payload:
                            body_html = payload.decode(charset, errors='replace')
                    except Exception as e:
                        logger.warning(f"Failed to decode HTML body: {e}")
        else:
            content_type = msg.get_content_type()
            try:
                charset = msg.get_content_charset() or 'utf-8'
                payload = msg.get_payload(decode=True)
                if payload:
                    if content_type == "text/html":
                        body_html = payload.decode(charset, errors='replace')
                    else:
                        body_text = payload.decode(charset, errors='replace')
            except Exception as e:
                logger.warning(f"Failed to decode body: {e}")
                
        return body_text, body_html
    
    def _has_attachments(self, msg: email.message.Message) -> bool:
        """Check if email has attachments"""
        if msg.is_multipart():
            for part in msg.walk():
                content_disposition = str(part.get("Content-Disposition", ""))
                if "attachment" in content_disposition:
                    return True
        return False
    
    async def connect_imap(self, settings: ProviderEmailSettings) -> aioimaplib.IMAP4_SSL:
        """Connect to IMAP server"""
        cache_key = f"{settings.username}@{settings.imap_host}"
        
        if cache_key in self._imap_connections:
            try:
                # Test if connection is still alive
                client = self._imap_connections[cache_key]
                if client.protocol and client.protocol.transport:
                    return client
            except:
                pass
            del self._imap_connections[cache_key]
        
        logger.info(f"🔌 Connecting to IMAP: {settings.imap_host}:{settings.imap_port}")
        
        try:
            if settings.imap_security == 'ssl':
                client = aioimaplib.IMAP4_SSL(
                    host=settings.imap_host,
                    port=settings.imap_port,
                    timeout=30
                )
            else:
                client = aioimaplib.IMAP4(
                    host=settings.imap_host,
                    port=settings.imap_port,
                    timeout=30
                )
            
            await client.wait_hello_from_server()
            
            if settings.imap_security == 'starttls':
                await client.starttls()
            
            await client.login(settings.username, settings.password)
            
            self._imap_connections[cache_key] = client
            logger.info(f"✅ IMAP connection established for {settings.username}")
            
            return client
            
        except Exception as e:
            logger.error(f"❌ IMAP connection failed: {e}")
            raise
    
    async def fetch_emails_imap(
        self,
        settings: ProviderEmailSettings,
        folder: str = "INBOX",
        max_results: int = 50,
        offset: int = 0
    ) -> List[EmailMessage]:
        """Fetch emails from IMAP server"""
        client = await self.connect_imap(settings)
        
        logger.info(f"📥 Fetching emails from {folder} via IMAP")
        
        await client.select(folder)
        
        # Search for all messages
        _, data = await client.search('ALL')
        message_numbers = data[0].split()
        
        # Get the most recent messages
        total = len(message_numbers)
        start = max(0, total - offset - max_results)
        end = total - offset
        
        message_numbers = message_numbers[start:end]
        message_numbers.reverse()  # Most recent first
        
        emails = []
        
        for msg_num in message_numbers[:max_results]:
            try:
                _, msg_data = await client.fetch(msg_num.decode(), '(RFC822 FLAGS)')
                
                if not msg_data or len(msg_data) < 2:
                    continue
                    
                raw_email = msg_data[1]
                if isinstance(raw_email, tuple):
                    raw_email = raw_email[1]
                    
                msg = email.message_from_bytes(raw_email)
                
                # Parse email details
                subject = self._decode_header_value(msg.get('Subject', ''))
                from_header = msg.get('From', '')
                from_name, from_address = parseaddr(from_header)
                from_name = self._decode_header_value(from_name) or from_address.split('@')[0]
                
                to_header = msg.get('To', '')
                to_name, to_address = parseaddr(to_header)
                to_name = self._decode_header_value(to_name) or to_address.split('@')[0] if to_address else ''
                
                cc_header = msg.get('Cc', '')
                
                date_str = msg.get('Date', '')
                try:
                    from email.utils import parsedate_to_datetime
                    date = parsedate_to_datetime(date_str)
                except:
                    date = datetime.now()
                
                message_id = msg.get('Message-ID', f"<{msg_num.decode()}@local>")
                
                body_text, body_html = self._extract_email_body(msg)
                has_attachments = self._has_attachments(msg)
                
                # Check if read (SEEN flag)
                flags_str = str(msg_data[0]) if msg_data[0] else ''
                is_read = '\\Seen' in flags_str
                
                email_msg = EmailMessage(
                    id=msg_num.decode(),
                    message_id=message_id,
                    thread_id=message_id,  # IMAP doesn't have native thread support
                    subject=subject or "(No subject)",
                    from_address=from_address,
                    from_name=from_name,
                    to_address=to_address,
                    to_name=to_name,
                    cc_address=cc_header if cc_header else None,
                    body_text=body_text,
                    body_html=body_html,
                    date=date,
                    is_read=is_read,
                    has_attachments=has_attachments,
                    folder=folder,
                    raw_email=raw_email
                )
                
                emails.append(email_msg)
                
            except Exception as e:
                logger.warning(f"Failed to parse email {msg_num}: {e}")
                continue
        
        logger.info(f"✅ Fetched {len(emails)} emails from {folder}")
        return emails
    
    def fetch_emails_pop3(
        self,
        settings: ProviderEmailSettings,
        max_results: int = 50
    ) -> List[EmailMessage]:
        """Fetch emails from POP3 server (synchronous)"""
        logger.info(f"📥 Connecting to POP3: {settings.imap_host}:{settings.imap_port}")
        
        try:
            # Create SSL context
            context = ssl.create_default_context()
            
            # Connect to POP3 server
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
            logger.info(f"📬 Found {num_messages} messages in POP3 mailbox")
            
            emails = []
            
            # Fetch most recent messages
            start = max(1, num_messages - max_results + 1)
            
            for i in range(num_messages, start - 1, -1):
                try:
                    # Retrieve message
                    response, lines, octets = pop.retr(i)
                    raw_email = b'\r\n'.join(lines)
                    
                    msg = email.message_from_bytes(raw_email)
                    
                    # Parse email details
                    subject = self._decode_header_value(msg.get('Subject', ''))
                    from_header = msg.get('From', '')
                    from_name, from_address = parseaddr(from_header)
                    from_name = self._decode_header_value(from_name) or from_address.split('@')[0]
                    
                    to_header = msg.get('To', '')
                    to_name, to_address = parseaddr(to_header)
                    to_name = self._decode_header_value(to_name) or to_address.split('@')[0] if to_address else ''
                    
                    cc_header = msg.get('Cc', '')
                    
                    date_str = msg.get('Date', '')
                    try:
                        from email.utils import parsedate_to_datetime
                        date = parsedate_to_datetime(date_str)
                    except:
                        date = datetime.now()
                    
                    message_id = msg.get('Message-ID', f"<{i}@pop3>")
                    
                    body_text, body_html = self._extract_email_body(msg)
                    has_attachments = self._has_attachments(msg)
                    
                    email_msg = EmailMessage(
                        id=str(i),
                        message_id=message_id,
                        thread_id=message_id,
                        subject=subject or "(No subject)",
                        from_address=from_address,
                        from_name=from_name,
                        to_address=to_address,
                        to_name=to_name,
                        cc_address=cc_header if cc_header else None,
                        body_text=body_text,
                        body_html=body_html,
                        date=date,
                        is_read=True,  # POP3 doesn't track read status
                        has_attachments=has_attachments,
                        folder="INBOX",
                        raw_email=raw_email
                    )
                    
                    emails.append(email_msg)
                    
                    if len(emails) >= max_results:
                        break
                        
                except Exception as e:
                    logger.warning(f"Failed to parse POP3 message {i}: {e}")
                    continue
            
            pop.quit()
            logger.info(f"✅ Fetched {len(emails)} emails via POP3")
            return emails
            
        except Exception as e:
            logger.error(f"❌ POP3 fetch failed: {e}")
            raise
    
    async def send_email_smtp(
        self,
        settings: ProviderEmailSettings,
        to_address: str,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
        cc_address: Optional[str] = None,
        bcc_address: Optional[str] = None,
        attachments: Optional[List[Dict]] = None,
        oauth_user_email: Optional[str] = None,
        oauth_access_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send email via SMTP

        Sending strategies (priority order):
        1) Gmail SMTP with OAuth (XOAUTH2) when oauth_access_token is provided.
        2) Gmail SMTP with App Password (GMAIL_SMTP_EMAIL + GMAIL_SMTP_APP_PASSWORD).
        3) SMTP Relay (SMTP_RELAY_HOST...).
        4) Direct provider SMTP.
        """
        # Strategy 1: Gmail SMTP via OAuth (XOAUTH2)
        use_gmail_oauth = bool(oauth_access_token and oauth_user_email)

        # Strategy 2: Gmail SMTP via App Password
        gmail_smtp_email = os.getenv("GMAIL_SMTP_EMAIL")
        gmail_smtp_password = os.getenv("GMAIL_SMTP_APP_PASSWORD")

        # Strategy 3: Generic SMTP relay (SMTP2GO, etc.)
        relay_host = os.getenv("SMTP_RELAY_HOST")
        relay_port = int(os.getenv("SMTP_RELAY_PORT") or 2525) if relay_host else settings.smtp_port
        relay_security = os.getenv("SMTP_RELAY_SECURITY", settings.smtp_security).lower()
        relay_username = os.getenv("SMTP_RELAY_USERNAME", settings.username)
        relay_password = os.getenv("SMTP_RELAY_PASSWORD", settings.password)

        # Determine which strategy to use
        use_gmail_smtp = bool(gmail_smtp_email and gmail_smtp_password) and not use_gmail_oauth
        use_relay = bool(relay_host) and not use_gmail_oauth and not use_gmail_smtp

        if use_gmail_oauth:
            smtp_host = "smtp.gmail.com"
            smtp_port = 587
            smtp_security = "starttls"
            smtp_username = oauth_user_email
            smtp_password = None  # XOAUTH2 uses token
            logger.info(f"📤 Using Gmail SMTP (OAuth) for {oauth_user_email}")
        elif use_gmail_smtp:
            smtp_host = "smtp.gmail.com"
            smtp_port = 587
            smtp_security = "starttls"
            smtp_username = gmail_smtp_email
            smtp_password = gmail_smtp_password
            logger.info(f"📤 Using Gmail SMTP (App Password) for {gmail_smtp_email}")
        elif use_relay:
            smtp_host = relay_host
            smtp_port = relay_port
            smtp_security = relay_security
            smtp_username = relay_username
            smtp_password = relay_password
            logger.info(f"📤 Using SMTP relay: {smtp_host}:{smtp_port}")
        else:
            smtp_host = settings.smtp_host
            smtp_port = settings.smtp_port
            smtp_security = settings.smtp_security
            smtp_username = settings.username
            smtp_password = settings.password
            logger.info(f"📤 Using direct SMTP: {smtp_host}:{smtp_port}")

        # Get user's actual email address (the one they want replies to go to)
        sender_email = settings.email or settings.username

        logger.info(
            f"📤 Sending to: {to_address} | On behalf of: {sender_email}"
        )
        
        try:
            # Create message
            if body_html:
                msg = MIMEMultipart('alternative')
                msg.attach(MIMEText(body_text, 'plain', 'utf-8'))
                msg.attach(MIMEText(body_html, 'html', 'utf-8'))
            else:
                msg = MIMEText(body_text, 'plain', 'utf-8')
            
            # Set From header based on sending strategy
            if use_gmail_oauth or use_gmail_smtp:
                # Gmail SMTP: Send on behalf with Reply-To to actual user
                gmail_from_name = os.getenv("GMAIL_SMTP_FROM_NAME", "QuMail Secure")
                from_email = oauth_user_email if use_gmail_oauth else gmail_smtp_email
                msg['From'] = f"{gmail_from_name} <{from_email}>"
                msg['Reply-To'] = sender_email
                msg['X-Original-Sender'] = sender_email
                logger.info(f"📧 Gmail SMTP ({'OAuth' if use_gmail_oauth else 'AppPwd'}): From={from_email}, Reply-To={sender_email}")
            elif use_relay:
                # SMTP Relay: May require verified sender
                relay_from_email = os.getenv("SMTP_RELAY_FROM_EMAIL")
                if relay_from_email:
                    relay_from_name = os.getenv("SMTP_RELAY_FROM_NAME", "QuMail Secure")
                    msg['From'] = f"{relay_from_name} <{relay_from_email}>"
                else:
                    msg['From'] = sender_email
                msg['Reply-To'] = sender_email
                msg['X-Original-Sender'] = sender_email
                logger.info(f"📧 Relay mode: Reply-To={sender_email}")
            else:
                # Direct SMTP - use user's actual email
                msg['From'] = sender_email
            
            msg['To'] = to_address
            msg['Subject'] = subject
            
            if cc_address:
                msg['Cc'] = cc_address
            
            # Build recipient list
            recipients = [to_address]
            if cc_address:
                recipients.extend([addr.strip() for addr in cc_address.split(',')])
            if bcc_address:
                recipients.extend([addr.strip() for addr in bcc_address.split(',')])
            
            # Connect and send
            if smtp_security == 'ssl':
                smtp = aiosmtplib.SMTP(
                    hostname=smtp_host,
                    port=smtp_port,
                    use_tls=True,
                    timeout=45,
                    validate_certs=False
                )
            else:
                smtp = aiosmtplib.SMTP(
                    hostname=smtp_host,
                    port=smtp_port,
                    start_tls=True if smtp_security == 'starttls' else False,
                    timeout=45
                )

            await smtp.connect()

            if use_gmail_oauth:
                # XOAUTH2 for Gmail
                auth_string = f"user={smtp_username}\x01auth=Bearer {oauth_access_token}\x01\x01"
                auth_b64 = base64.b64encode(auth_string.encode()).decode()
                code, resp = await smtp.execute_command("AUTH", "XOAUTH2", auth_b64)
                if code != 235:
                    await smtp.quit()
                    raise RuntimeError(f"Gmail XOAUTH2 failed: {code} {resp}")
            else:
                await smtp.login(smtp_username, smtp_password)

            await smtp.send_message(msg, recipients=recipients)
            await smtp.quit()

            logger.info(f"✅ Email sent successfully to {to_address}")
            
            return {
                "success": True,
                "message_id": msg.get('Message-ID'),
                "from": sender_email,
                "to": to_address,
                "subject": subject,
                "relay": use_relay,
                "reply_to": sender_email if use_relay else None
            }
            
        except Exception as e:
            logger.error(f"❌ SMTP send failed: {e}")
            raise
    
    async def list_folders_imap(self, settings: ProviderEmailSettings) -> List[str]:
        """List available folders via IMAP"""
        client = await self.connect_imap(settings)
        
        _, data = await client.list(reference_name="", mailbox_pattern="*")
        
        folders = []
        for folder_data in data:
            if isinstance(folder_data, bytes):
                # Parse folder name from response like: b'(\\HasNoChildren) "/" "INBOX"'
                try:
                    parts = folder_data.decode().split('"')
                    if len(parts) >= 4:
                        folder_name = parts[-2]
                        folders.append(folder_name)
                except:
                    pass
        
        return folders
    
    async def fetch_new_emails_since(
        self,
        settings: ProviderEmailSettings,
        since_message_id: Optional[str] = None,
        folder: str = "INBOX",
        max_results: int = 10
    ) -> Tuple[List[EmailMessage], int]:
        """
        Fetch only new emails since the given message_id.
        
        Returns:
            Tuple of (new_emails, total_new_count)
        """
        client = await self.connect_imap(settings)
        
        logger.info(f"📥 Checking for new emails in {folder} since {since_message_id}")
        
        await client.select(folder)
        
        # Search for all messages
        _, data = await client.search('ALL')
        message_numbers = data[0].split()
        
        total = len(message_numbers)
        
        if total == 0:
            return [], 0
        
        # Get the most recent emails
        message_numbers = message_numbers[-max_results:]
        message_numbers.reverse()  # Most recent first
        
        new_emails = []
        found_existing = False
        
        for msg_num in message_numbers:
            try:
                _, msg_data = await client.fetch(msg_num.decode(), '(RFC822 FLAGS)')
                
                if not msg_data or len(msg_data) < 2:
                    continue
                    
                raw_email = msg_data[1]
                if isinstance(raw_email, tuple):
                    raw_email = raw_email[1]
                    
                msg = email.message_from_bytes(raw_email)
                
                msg_id = msg.get('Message-ID', '')
                
                # If we've reached the last known message, stop
                if since_message_id and msg_id == since_message_id:
                    found_existing = True
                    break
                
                # Parse email details
                subject = self._decode_header_value(msg.get('Subject', ''))
                from_header = msg.get('From', '')
                from_name, from_address = parseaddr(from_header)
                from_name = self._decode_header_value(from_name) or from_address.split('@')[0]
                
                to_header = msg.get('To', '')
                to_name, to_address = parseaddr(to_header)
                to_name = self._decode_header_value(to_name) or to_address.split('@')[0] if to_address else ''
                
                cc_header = msg.get('Cc', '')
                
                date_str = msg.get('Date', '')
                try:
                    from email.utils import parsedate_to_datetime
                    date = parsedate_to_datetime(date_str)
                except:
                    date = datetime.now()
                
                body_text, body_html = self._extract_email_body(msg)
                
                # Determine read status from FLAGS
                is_read = b'\\Seen' in msg_data[0] if msg_data[0] else False
                
                email_msg = EmailMessage(
                    id=msg_num.decode(),
                    message_id=msg_id,
                    thread_id=msg.get('References', msg_id)[:64] if msg.get('References') else msg_id,
                    subject=subject,
                    from_address=from_address,
                    from_name=from_name,
                    to_address=to_address,
                    to_name=to_name,
                    cc_address=cc_header if cc_header else None,
                    body_text=body_text,
                    body_html=body_html,
                    date=date,
                    is_read=is_read,
                    has_attachments=self._has_attachments(msg),
                    folder=folder,
                    raw_email=raw_email
                )
                
                new_emails.append(email_msg)
                
            except Exception as e:
                logger.warning(f"Failed to parse email {msg_num}: {e}")
                continue
        
        new_count = len(new_emails)
        logger.info(f"✅ Found {new_count} new emails in {folder}")
        
        return new_emails, new_count
    
    async def mark_as_read_imap(
        self,
        settings: ProviderEmailSettings,
        message_id: str,
        folder: str = "INBOX"
    ) -> bool:
        """Mark email as read via IMAP"""
        client = await self.connect_imap(settings)
        
        await client.select(folder)
        await client.store(message_id, '+FLAGS', '\\Seen')
        
        return True
    
    async def delete_email_imap(
        self,
        settings: ProviderEmailSettings,
        message_id: str,
        folder: str = "INBOX"
    ) -> bool:
        """Delete email via IMAP"""
        client = await self.connect_imap(settings)
        
        await client.select(folder)
        await client.store(message_id, '+FLAGS', '\\Deleted')
        await client.expunge()
        
        return True
    
    async def close_connection(self, settings: ProviderEmailSettings):
        """Close IMAP connection"""
        cache_key = f"{settings.username}@{settings.imap_host}"
        
        if cache_key in self._imap_connections:
            try:
                client = self._imap_connections[cache_key]
                await client.logout()
            except:
                pass
            del self._imap_connections[cache_key]


# Singleton instance
multi_provider_client = MultiProviderEmailClient()
