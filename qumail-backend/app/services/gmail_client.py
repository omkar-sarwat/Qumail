import asyncio
import base64
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import aiohttp
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import email
from email.header import decode_header
from ..config import get_settings
from ..schemas import SecurityLevel
from ..services.gmail_oauth import oauth_service
from ..services.security_auditor import security_auditor, SecurityIncidentType
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
settings = get_settings()

class GmailError(Exception):
    """Gmail API related errors"""
    pass

class GmailClient:
    """Secure Gmail client with comprehensive error handling"""
    
    def __init__(self):
        self.base_url = "https://gmail.googleapis.com/gmail/v1/users/me"
        self.max_retries = 3
        self.timeout = 30
    
    async def get_messages(
        self, 
        user_email: str, 
        session: AsyncSession,
        query: str = "",
        max_results: int = 50,
        page_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get Gmail messages with security validation
        
        Args:
            user_email: User's email address
            session: Database session
            query: Gmail search query (optional)
            max_results: Maximum number of results (1-500)
            page_token: Pagination token
        
        Returns:
            Dict containing messages and nextPageToken
        """
        try:
            # Get valid access token
            access_token = await oauth_service.get_valid_access_token(user_email, session)
            
            # Build request parameters
            params = {
                "maxResults": min(max_results, 500),  # Gmail API limit
                "includeSpamTrash": False,  # Security: exclude spam/trash by default
            }
            
            if query:
                params["q"] = query
            if page_token:
                params["pageToken"] = page_token
            
            # Make API request with security headers
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
                "User-Agent": f"QuMail/{settings.app_version}"
            }
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as client:
                async with client.get(
                    f"{self.base_url}/messages",
                    headers=headers,
                    params=params
                ) as response:
                    
                    if response.status == 401:
                        # Token expired, try refresh
                        logger.info(f"Token expired for {user_email}, attempting refresh")
                        access_token = await oauth_service.refresh_access_token(user_email, session)
                        headers["Authorization"] = f"Bearer {access_token}"
                        
                        # Retry with new token
                        async with client.get(
                            f"{self.base_url}/messages",
                            headers=headers,
                            params=params
                        ) as retry_response:
                            if retry_response.status != 200:
                                error_text = await retry_response.text()
                                raise GmailError(f"Failed to fetch messages: {error_text}")
                            return await retry_response.json()
                    
                    elif response.status != 200:
                        error_text = await response.text()
                        await security_auditor.log_incident(
                            SecurityIncidentType.API_ERROR,
                            f"Gmail API error for {user_email}: {response.status}",
                            user_id=user_email,
                            details={"status": response.status, "response": error_text}
                        )
                        raise GmailError(f"Failed to fetch messages: {error_text}")
                    
                    result = await response.json()
                    
                    # Log successful access
                    logger.info(f"Retrieved {len(result.get('messages', []))} messages for {user_email}")
                    
                    return result
        
        except Exception as e:
            logger.error(f"Error fetching messages for {user_email}: {e}")
            await security_auditor.log_incident(
                SecurityIncidentType.API_ERROR,
                f"Gmail fetch error: {str(e)}",
                user_id=user_email,
                details={"error": str(e), "query": query}
            )
            raise GmailError(f"Failed to fetch messages: {e}")
    
    async def get_message_details(
        self, 
        user_email: str, 
        message_id: str,
        session: AsyncSession,
        format: str = "full"
    ) -> Dict[str, Any]:
        """
        Get detailed message information
        
        Args:
            user_email: User's email address
            message_id: Gmail message ID
            session: Database session
            format: Message format (minimal, full, raw, metadata)
        
        Returns:
            Complete message data including headers and body
        """
        try:
            # Get valid access token
            access_token = await oauth_service.get_valid_access_token(user_email, session)
            
            # Security validation: ensure format is safe
            allowed_formats = ["minimal", "full", "raw", "metadata"]
            if format not in allowed_formats:
                format = "full"
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
                "User-Agent": f"QuMail/{settings.app_version}"
            }
            
            params = {"format": format}
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as client:
                async with client.get(
                    f"{self.base_url}/messages/{message_id}",
                    headers=headers,
                    params=params
                ) as response:
                    
                    if response.status == 401:
                        # Token expired, refresh and retry
                        access_token = await oauth_service.refresh_access_token(user_email, session)
                        headers["Authorization"] = f"Bearer {access_token}"
                        
                        async with client.get(
                            f"{self.base_url}/messages/{message_id}",
                            headers=headers,
                            params=params
                        ) as retry_response:
                            if retry_response.status != 200:
                                error_text = await retry_response.text()
                                raise GmailError(f"Failed to fetch message: {error_text}")
                            return await retry_response.json()
                    
                    elif response.status != 200:
                        error_text = await response.text()
                        raise GmailError(f"Failed to fetch message: {error_text}")
                    
                    message_data = await response.json()
                    
                    # Security: Log access to message details
                    logger.info(f"Retrieved message {message_id} for {user_email}")
                    
                    return message_data
        
        except Exception as e:
            logger.error(f"Error fetching message {message_id} for {user_email}: {e}")
            await security_auditor.log_incident(
                SecurityIncidentType.API_ERROR,
                f"Gmail message fetch error: {str(e)}",
                user_id=user_email,
                details={"error": str(e), "message_id": message_id}
            )
            raise GmailError(f"Failed to fetch message: {e}")
    
    async def send_message(
        self,
        user_email: str,
        to_addresses: List[str],
        subject: str,
        body: str,
        session: AsyncSession,
        security_level: SecurityLevel = SecurityLevel.LEVEL_1,
        cc_addresses: Optional[List[str]] = None,
        bcc_addresses: Optional[List[str]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Send secure email with chosen security level
        
        Args:
            user_email: Sender's email address
            to_addresses: List of recipient email addresses
            subject: Email subject
            body: Email body (can be HTML or plain text)
            session: Database session
            security_level: Encryption level to use
            cc_addresses: CC recipients (optional)
            bcc_addresses: BCC recipients (optional)
            attachments: List of attachments (optional)
        
        Returns:
            Gmail API response with message ID
        """
        try:
            # Input validation and sanitization
            if not to_addresses:
                raise GmailError("At least one recipient is required")
            
            # Security: Validate email addresses
            for email_addr in to_addresses + (cc_addresses or []) + (bcc_addresses or []):
                if not self._is_valid_email(email_addr):
                    raise GmailError(f"Invalid email address: {email_addr}")
            
            # Get valid access token
            access_token = await oauth_service.get_valid_access_token(user_email, session)
            
            # Create MIME message
            message = MIMEMultipart('alternative')
            message['From'] = user_email
            message['To'] = ', '.join(to_addresses)
            message['Subject'] = subject
            
            if cc_addresses:
                message['Cc'] = ', '.join(cc_addresses)
            if bcc_addresses:
                message['Bcc'] = ', '.join(bcc_addresses)
            
            # Add security level indicator to headers
            message['X-QuMail-Security-Level'] = security_level.value
            message['X-QuMail-Version'] = settings.app_version
            
            # Add body (support both plain text and HTML)
            if body.strip().startswith('<'):
                # HTML body
                html_part = MIMEText(body, 'html', 'utf-8')
                message.attach(html_part)
            else:
                # Plain text body
                text_part = MIMEText(body, 'plain', 'utf-8')
                message.attach(text_part)
            
            # Add attachments if provided
            if attachments:
                for attachment in attachments:
                    self._add_attachment(message, attachment)
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # Prepare API request
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "User-Agent": f"QuMail/{settings.app_version}"
            }
            
            payload = {
                "raw": raw_message
            }
            
            # Send message via Gmail API
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as client:
                async with client.post(
                    f"{self.base_url}/messages/send",
                    headers=headers,
                    json=payload
                ) as response:
                    
                    if response.status == 401:
                        # Token expired, refresh and retry
                        access_token = await oauth_service.refresh_access_token(user_email, session)
                        headers["Authorization"] = f"Bearer {access_token}"
                        
                        async with client.post(
                            f"{self.base_url}/messages/send",
                            headers=headers,
                            json=payload
                        ) as retry_response:
                            if retry_response.status != 200:
                                error_text = await retry_response.text()
                                raise GmailError(f"Failed to send message: {error_text}")
                            result = await retry_response.json()
                    
                    elif response.status != 200:
                        error_text = await response.text()
                        await security_auditor.log_incident(
                            SecurityIncidentType.API_ERROR,
                            f"Gmail send error for {user_email}: {response.status}",
                            user_id=user_email,
                            details={"status": response.status, "response": error_text}
                        )
                        raise GmailError(f"Failed to send message: {error_text}")
                    else:
                        result = await response.json()
                    
                    # Log successful send
                    logger.info(f"Message sent by {user_email} to {len(to_addresses)} recipients with {security_level.value} security")
                    
                    # Store in database for security tracking
                    await self._store_sent_email(
                        session, user_email, to_addresses, subject, 
                        security_level, result['id']
                    )
                    
                    return result
        
        except Exception as e:
            logger.error(f"Error sending message from {user_email}: {e}")
            await security_auditor.log_incident(
                SecurityIncidentType.API_ERROR,
                f"Gmail send error: {str(e)}",
                user_id=user_email,
                details={"error": str(e), "recipients": to_addresses}
            )
            raise GmailError(f"Failed to send message: {e}")
    
    async def modify_message(
        self,
        user_email: str,
        message_id: str,
        add_label_ids: Optional[List[str]] = None,
        remove_label_ids: Optional[List[str]] = None,
        session: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """
        Modify message labels (mark as read, add labels, etc.)
        """
        try:
            access_token = await oauth_service.get_valid_access_token(user_email, session)
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "User-Agent": f"QuMail/{settings.app_version}"
            }
            
            payload = {}
            if add_label_ids:
                payload["addLabelIds"] = add_label_ids
            if remove_label_ids:
                payload["removeLabelIds"] = remove_label_ids
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as client:
                async with client.post(
                    f"{self.base_url}/messages/{message_id}/modify",
                    headers=headers,
                    json=payload
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        raise GmailError(f"Failed to modify message: {error_text}")
                    
                    return await response.json()
        
        except Exception as e:
            logger.error(f"Error modifying message {message_id} for {user_email}: {e}")
            raise GmailError(f"Failed to modify message: {e}")
    
    async def get_labels(self, user_email: str, session: AsyncSession) -> List[Dict[str, Any]]:
        """Get user's Gmail labels"""
        try:
            access_token = await oauth_service.get_valid_access_token(user_email, session)
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
                "User-Agent": f"QuMail/{settings.app_version}"
            }
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as client:
                async with client.get(
                    f"{self.base_url}/labels",
                    headers=headers
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        raise GmailError(f"Failed to fetch labels: {error_text}")
                    
                    result = await response.json()
                    return result.get('labels', [])
        
        except Exception as e:
            logger.error(f"Error fetching labels for {user_email}: {e}")
            raise GmailError(f"Failed to fetch labels: {e}")
    
    def parse_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Gmail message data into readable format
        
        Returns:
            Parsed message with headers, body, and metadata
        """
        try:
            # Extract basic info
            message_id = message_data.get('id', '')
            thread_id = message_data.get('threadId', '')
            label_ids = message_data.get('labelIds', [])
            snippet = message_data.get('snippet', '')
            
            # Parse payload
            payload = message_data.get('payload', {})
            headers = payload.get('headers', [])
            
            # Extract headers
            header_dict = {}
            for header in headers:
                name = header.get('name', '').lower()
                value = header.get('value', '')
                header_dict[name] = value
            
            # Extract body
            body_data = self._extract_body(payload)
            
            # Check for QuMail security level
            security_level = header_dict.get('x-qumail-security-level', 'NONE')
            
            return {
                'id': message_id,
                'thread_id': thread_id,
                'labels': label_ids,
                'snippet': snippet,
                'subject': header_dict.get('subject', ''),
                'from': header_dict.get('from', ''),
                'to': header_dict.get('to', ''),
                'cc': header_dict.get('cc', ''),
                'date': header_dict.get('date', ''),
                'body_text': body_data.get('text', ''),
                'body_html': body_data.get('html', ''),
                'security_level': security_level,
                'has_attachments': self._has_attachments(payload),
                'raw_headers': header_dict
            }
        
        except Exception as e:
            logger.error(f"Error parsing message: {e}")
            return {
                'id': message_data.get('id', ''),
                'error': f"Failed to parse message: {e}"
            }
    
    # Private helper methods
    
    def _is_valid_email(self, email_addr: str) -> bool:
        """Basic email validation"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email_addr) is not None
    
    def _add_attachment(self, message: MIMEMultipart, attachment: Dict[str, Any]):
        """Add attachment to MIME message"""
        try:
            filename = attachment.get('filename', 'attachment')
            content = attachment.get('content', b'')
            content_type = attachment.get('content_type', 'application/octet-stream')
            
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(content)
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {filename}'
            )
            message.attach(part)
        
        except Exception as e:
            logger.error(f"Error adding attachment: {e}")
    
    async def _store_sent_email(
        self,
        session: AsyncSession,
        sender: str,
        recipients: List[str],
        subject: str,
        security_level: SecurityLevel,
        gmail_message_id: str
    ):
        """Store sent email in database for tracking"""
        try:
            email_record = Email(
                sender=sender,
                recipient=recipients[0],  # Primary recipient
                subject=subject,
                security_level=security_level,
                gmail_message_id=gmail_message_id,
                sent_at=datetime.utcnow()
            )
            
            session.add(email_record)
            await session.commit()
        
        except Exception as e:
            logger.error(f"Error storing sent email: {e}")
    
    def _extract_body(self, payload: Dict[str, Any]) -> Dict[str, str]:
        """Extract text and HTML body from message payload"""
        body_data = {'text': '', 'html': ''}
        
        try:
            if 'body' in payload and payload['body'].get('data'):
                # Single part message
                body_text = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
                if payload.get('mimeType') == 'text/html':
                    body_data['html'] = body_text
                else:
                    body_data['text'] = body_text
            
            elif 'parts' in payload:
                # Multi-part message
                for part in payload['parts']:
                    mime_type = part.get('mimeType', '')
                    if 'body' in part and part['body'].get('data'):
                        content = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        if mime_type == 'text/plain':
                            body_data['text'] = content
                        elif mime_type == 'text/html':
                            body_data['html'] = content
        
        except Exception as e:
            logger.error(f"Error extracting body: {e}")
        
        return body_data
    
    def _has_attachments(self, payload: Dict[str, Any]) -> bool:
        """Check if message has attachments"""
        try:
            if 'parts' in payload:
                for part in payload['parts']:
                    disposition = ''
                    for header in part.get('headers', []):
                        if header['name'].lower() == 'content-disposition':
                            disposition = header['value'].lower()
                            break
                    
                    if 'attachment' in disposition:
                        return True
            
            return False
        
        except Exception:
            return False

# Global Gmail client instance
gmail_client = GmailClient()
