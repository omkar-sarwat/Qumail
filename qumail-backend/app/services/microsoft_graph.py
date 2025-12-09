"""
Microsoft Graph API Client for Email Operations
Handles fetching and sending emails via Microsoft Graph API for Outlook/Microsoft 365
"""

import logging
import aiohttp
import base64
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, EmailStr
from motor.motor_asyncio import AsyncIOMotorDatabase

from .microsoft_oauth import microsoft_oauth_service, MicrosoftOAuthError, MicrosoftTokenError

logger = logging.getLogger(__name__)


class GraphEmail(BaseModel):
    """Email model for Microsoft Graph API"""
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
    date: datetime
    is_read: bool
    has_attachments: bool
    folder: str = "inbox"
    importance: str = "normal"


class GraphSendResult(BaseModel):
    """Result from sending email via Graph API"""
    success: bool
    message_id: Optional[str] = None
    message: str


class MicrosoftGraphClient:
    """Microsoft Graph API client for email operations"""
    
    GRAPH_ENDPOINT = "https://graph.microsoft.com/v1.0"
    
    def __init__(self):
        pass
    
    async def _get_headers(self, user_email: str, db: AsyncIOMotorDatabase) -> Dict[str, str]:
        """Get authorization headers for Graph API calls"""
        try:
            access_token = await microsoft_oauth_service.get_valid_access_token(user_email, db)
            return {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
        except Exception as e:
            logger.error(f"Failed to get access token for {user_email}: {e}")
            raise MicrosoftOAuthError(f"Failed to authenticate: {e}")
    
    async def fetch_emails(
        self,
        user_email: str,
        db: AsyncIOMotorDatabase,
        folder: str = "inbox",
        max_results: int = 50,
        skip: int = 0,
        filter_unread: bool = False
    ) -> List[GraphEmail]:
        """
        Fetch emails from Microsoft Graph API
        
        Args:
            user_email: The user's email address (for token lookup)
            db: MongoDB database connection
            folder: Mail folder to fetch from (inbox, sentitems, drafts, etc.)
            max_results: Maximum number of emails to fetch
            skip: Number of emails to skip (for pagination)
            filter_unread: If True, only fetch unread emails
        
        Returns:
            List of GraphEmail objects
        """
        try:
            headers = await self._get_headers(user_email, db)
            
            # Map folder names to Graph API folder names
            folder_map = {
                "inbox": "inbox",
                "sent": "sentitems",
                "sentitems": "sentitems",
                "drafts": "drafts",
                "trash": "deleteditems",
                "junk": "junkemail",
                "spam": "junkemail",
                "archive": "archive"
            }
            graph_folder = folder_map.get(folder.lower(), folder)
            
            # Build URL with query parameters
            url = f"{self.GRAPH_ENDPOINT}/me/mailFolders/{graph_folder}/messages"
            
            params = {
                "$top": max_results,
                "$skip": skip,
                "$orderby": "receivedDateTime desc",
                "$select": "id,internetMessageId,conversationId,subject,from,toRecipients,ccRecipients,body,bodyPreview,receivedDateTime,isRead,hasAttachments,importance"
            }
            
            if filter_unread:
                params["$filter"] = "isRead eq false"
            
            # Build query string
            query_string = "&".join(f"{k}={v}" for k, v in params.items())
            url = f"{url}?{query_string}"
            
            logger.info(f"Fetching emails from Microsoft Graph: {url[:100]}...")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 401:
                        # Try to refresh token and retry
                        logger.info("Token expired, refreshing...")
                        await microsoft_oauth_service.refresh_access_token(user_email, db)
                        headers = await self._get_headers(user_email, db)
                        async with session.get(url, headers=headers) as retry_response:
                            if retry_response.status != 200:
                                error_text = await retry_response.text()
                                raise MicrosoftOAuthError(f"Failed to fetch emails after token refresh: {error_text}")
                            data = await retry_response.json()
                    elif response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Graph API error: {error_text}")
                        raise MicrosoftOAuthError(f"Failed to fetch emails: {error_text}")
                    else:
                        data = await response.json()
            
            # Parse emails
            emails = []
            for msg in data.get("value", []):
                try:
                    email = self._parse_graph_message(msg, folder)
                    emails.append(email)
                except Exception as e:
                    logger.warning(f"Failed to parse email {msg.get('id')}: {e}")
                    continue
            
            logger.info(f"Fetched {len(emails)} emails from Microsoft Graph")
            return emails
            
        except MicrosoftOAuthError:
            raise
        except Exception as e:
            logger.error(f"Error fetching emails from Graph API: {e}")
            raise MicrosoftOAuthError(f"Failed to fetch emails: {e}")
    
    def _parse_graph_message(self, msg: Dict[str, Any], folder: str) -> GraphEmail:
        """Parse a Graph API message into GraphEmail model"""
        from_data = msg.get("from", {}).get("emailAddress", {})
        to_recipients = msg.get("toRecipients", [])
        cc_recipients = msg.get("ccRecipients", [])
        
        # Get first recipient for to_address
        to_data = to_recipients[0].get("emailAddress", {}) if to_recipients else {}
        
        # Parse CC addresses
        cc_addresses = ", ".join(
            r.get("emailAddress", {}).get("address", "")
            for r in cc_recipients
        ) if cc_recipients else None
        
        # Parse body
        body_data = msg.get("body", {})
        body_content = body_data.get("content", "")
        body_type = body_data.get("contentType", "text")
        
        # Determine body_text and body_html
        if body_type.lower() == "html":
            body_html = body_content
            # Extract plain text from HTML (basic)
            import re
            body_text = re.sub(r'<[^>]+>', '', body_content)
            body_text = body_text.replace('&nbsp;', ' ').strip()
        else:
            body_text = body_content
            body_html = None
        
        # Parse date
        received_str = msg.get("receivedDateTime", "")
        try:
            received_date = datetime.fromisoformat(received_str.replace("Z", "+00:00"))
        except:
            received_date = datetime.utcnow()
        
        return GraphEmail(
            id=msg.get("id", ""),
            message_id=msg.get("internetMessageId", msg.get("id", "")),
            thread_id=msg.get("conversationId", ""),
            subject=msg.get("subject", "(No Subject)"),
            from_address=from_data.get("address", ""),
            from_name=from_data.get("name", ""),
            to_address=to_data.get("address", ""),
            to_name=to_data.get("name", ""),
            cc_address=cc_addresses,
            body_text=body_text,
            body_html=body_html,
            date=received_date,
            is_read=msg.get("isRead", False),
            has_attachments=msg.get("hasAttachments", False),
            folder=folder,
            importance=msg.get("importance", "normal")
        )
    
    async def send_email(
        self,
        user_email: str,
        db: AsyncIOMotorDatabase,
        to_address: str,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
        cc_address: Optional[str] = None,
        bcc_address: Optional[str] = None,
        save_to_sent: bool = True
    ) -> GraphSendResult:
        """
        Send email via Microsoft Graph API
        
        Args:
            user_email: The sender's email address (for token lookup)
            db: MongoDB database connection
            to_address: Recipient email address(es), comma-separated
            subject: Email subject
            body_text: Plain text body
            body_html: Optional HTML body
            cc_address: Optional CC address(es), comma-separated
            bcc_address: Optional BCC address(es), comma-separated
            save_to_sent: Whether to save the email to Sent Items
        
        Returns:
            GraphSendResult with success status and message ID
        """
        try:
            headers = await self._get_headers(user_email, db)
            
            # Build message payload
            message = {
                "subject": subject,
                "body": {
                    "contentType": "HTML" if body_html else "Text",
                    "content": body_html or body_text
                },
                "toRecipients": [
                    {"emailAddress": {"address": addr.strip()}}
                    for addr in to_address.split(",")
                ]
            }
            
            # Add CC recipients
            if cc_address:
                message["ccRecipients"] = [
                    {"emailAddress": {"address": addr.strip()}}
                    for addr in cc_address.split(",")
                ]
            
            # Add BCC recipients
            if bcc_address:
                message["bccRecipients"] = [
                    {"emailAddress": {"address": addr.strip()}}
                    for addr in bcc_address.split(",")
                ]
            
            # Send email
            url = f"{self.GRAPH_ENDPOINT}/me/sendMail"
            payload = {
                "message": message,
                "saveToSentItems": save_to_sent
            }
            
            logger.info(f"Sending email via Microsoft Graph to: {to_address}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 401:
                        # Try to refresh token and retry
                        logger.info("Token expired, refreshing...")
                        await microsoft_oauth_service.refresh_access_token(user_email, db)
                        headers = await self._get_headers(user_email, db)
                        async with session.post(url, headers=headers, json=payload) as retry_response:
                            if retry_response.status != 202:
                                error_text = await retry_response.text()
                                raise MicrosoftOAuthError(f"Failed to send email after token refresh: {error_text}")
                    elif response.status != 202:
                        error_text = await response.text()
                        logger.error(f"Graph API send error: {error_text}")
                        raise MicrosoftOAuthError(f"Failed to send email: {error_text}")
            
            logger.info(f"Email sent successfully via Microsoft Graph to: {to_address}")
            
            return GraphSendResult(
                success=True,
                message_id=None,  # Graph API doesn't return message ID for sendMail
                message="Email sent successfully via Microsoft Graph"
            )
            
        except MicrosoftOAuthError:
            raise
        except Exception as e:
            logger.error(f"Error sending email via Graph API: {e}")
            return GraphSendResult(
                success=False,
                message=f"Failed to send email: {e}"
            )
    
    async def mark_as_read(
        self,
        user_email: str,
        db: AsyncIOMotorDatabase,
        message_id: str,
        is_read: bool = True
    ) -> bool:
        """Mark an email as read or unread"""
        try:
            headers = await self._get_headers(user_email, db)
            
            url = f"{self.GRAPH_ENDPOINT}/me/messages/{message_id}"
            payload = {"isRead": is_read}
            
            async with aiohttp.ClientSession() as session:
                async with session.patch(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        logger.info(f"Marked email {message_id} as {'read' if is_read else 'unread'}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to mark email: {error_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error marking email as read: {e}")
            return False
    
    async def delete_email(
        self,
        user_email: str,
        db: AsyncIOMotorDatabase,
        message_id: str
    ) -> bool:
        """Delete (move to trash) an email"""
        try:
            headers = await self._get_headers(user_email, db)
            
            # Move to deleted items (soft delete)
            url = f"{self.GRAPH_ENDPOINT}/me/messages/{message_id}/move"
            payload = {"destinationId": "deleteditems"}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 201:
                        logger.info(f"Moved email {message_id} to trash")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to delete email: {error_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error deleting email: {e}")
            return False
    
    async def get_unread_count(
        self,
        user_email: str,
        db: AsyncIOMotorDatabase,
        folder: str = "inbox"
    ) -> int:
        """Get count of unread emails in a folder"""
        try:
            headers = await self._get_headers(user_email, db)
            
            folder_map = {
                "inbox": "inbox",
                "sent": "sentitems",
                "drafts": "drafts"
            }
            graph_folder = folder_map.get(folder.lower(), folder)
            
            url = f"{self.GRAPH_ENDPOINT}/me/mailFolders/{graph_folder}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("unreadItemCount", 0)
                    else:
                        return 0
                        
        except Exception as e:
            logger.error(f"Error getting unread count: {e}")
            return 0


# Global client instance
microsoft_graph_client = MicrosoftGraphClient()
