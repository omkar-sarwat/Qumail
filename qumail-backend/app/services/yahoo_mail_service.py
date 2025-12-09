"""
Yahoo Mail Service - Send and receive emails via Yahoo Mail API
Uses Yahoo OAuth tokens for authentication
"""

import logging
import base64
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, List, Dict, Any
from datetime import datetime
import httpx
import json

logger = logging.getLogger(__name__)


class YahooMailService:
    """
    Yahoo Mail Service for sending and receiving emails
    Uses Yahoo Mail REST API with OAuth 2.0 tokens
    """
    
    # Yahoo Mail API endpoint
    MAIL_API_BASE = "https://mail.yahooapis.com/ws/mail/v3.0"
    
    def __init__(self):
        """Initialize Yahoo Mail service"""
        self.http_client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self, access_token: str) -> httpx.AsyncClient:
        """Get HTTP client with auth headers"""
        if self.http_client is None:
            self.http_client = httpx.AsyncClient(timeout=30.0)
        return self.http_client
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        access_token: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make authenticated request to Yahoo Mail API"""
        client = await self._get_client(access_token)
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        url = f"{self.MAIL_API_BASE}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = await client.get(url, headers=headers, params=params)
            elif method.upper() == "POST":
                response = await client.post(url, headers=headers, json=data)
            elif method.upper() == "DELETE":
                response = await client.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            
            if response.content:
                return response.json()
            return {"success": True}
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Yahoo Mail API error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Yahoo Mail API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Yahoo Mail request failed: {str(e)}")
            raise
    
    async def get_folders(self, access_token: str) -> List[Dict[str, Any]]:
        """
        Get list of email folders (Inbox, Sent, Drafts, etc.)
        
        Args:
            access_token: Valid Yahoo OAuth access token
            
        Returns:
            List of folder objects with id and name
        """
        try:
            response = await self._make_request("GET", "/folders", access_token)
            
            folders = response.get("folders", [])
            logger.info(f"Retrieved {len(folders)} Yahoo Mail folders")
            
            return folders
            
        except Exception as e:
            logger.error(f"Failed to get Yahoo Mail folders: {str(e)}")
            raise
    
    async def get_inbox_messages(
        self,
        access_token: str,
        count: int = 20,
        offset: int = 0,
        folder_id: str = "Inbox"
    ) -> Dict[str, Any]:
        """
        Get messages from inbox or specified folder
        
        Args:
            access_token: Valid Yahoo OAuth access token
            count: Number of messages to retrieve
            offset: Offset for pagination
            folder_id: Folder to fetch from (default: Inbox)
            
        Returns:
            Dict with messages array and total count
        """
        try:
            params = {
                "count": count,
                "start": offset,
                "fid": folder_id
            }
            
            response = await self._make_request(
                "GET", 
                "/messages", 
                access_token,
                params=params
            )
            
            messages = response.get("messages", [])
            total = response.get("total", len(messages))
            
            logger.info(f"Retrieved {len(messages)} messages from Yahoo {folder_id}")
            
            # Transform to common format
            formatted_messages = []
            for msg in messages:
                formatted_messages.append({
                    "id": msg.get("mid"),
                    "threadId": msg.get("tid"),
                    "subject": msg.get("subject", "(No Subject)"),
                    "from": self._format_address(msg.get("from")),
                    "to": [self._format_address(addr) for addr in msg.get("to", [])],
                    "date": msg.get("receivedDate"),
                    "snippet": msg.get("snippet", ""),
                    "isRead": msg.get("isRead", False),
                    "hasAttachment": msg.get("hasAttachment", False),
                    "labels": [folder_id],
                    "provider": "yahoo"
                })
            
            return {
                "messages": formatted_messages,
                "total": total,
                "count": len(formatted_messages)
            }
            
        except Exception as e:
            logger.error(f"Failed to get Yahoo inbox messages: {str(e)}")
            raise
    
    def _format_address(self, addr: Any) -> Dict[str, str]:
        """Format email address to common format"""
        if isinstance(addr, dict):
            return {
                "email": addr.get("email", ""),
                "name": addr.get("name", "")
            }
        elif isinstance(addr, str):
            return {"email": addr, "name": ""}
        return {"email": "", "name": ""}
    
    async def get_message(
        self,
        access_token: str,
        message_id: str
    ) -> Dict[str, Any]:
        """
        Get full message details
        
        Args:
            access_token: Valid Yahoo OAuth access token
            message_id: Message ID to retrieve
            
        Returns:
            Full message object with body and headers
        """
        try:
            response = await self._make_request(
                "GET",
                f"/messages/{message_id}",
                access_token
            )
            
            msg = response.get("message", response)
            
            # Extract body content
            body_html = ""
            body_text = ""
            
            parts = msg.get("parts", [])
            for part in parts:
                content_type = part.get("contentType", "")
                if "text/html" in content_type:
                    body_html = part.get("body", "")
                elif "text/plain" in content_type:
                    body_text = part.get("body", "")
            
            if not body_html and not body_text:
                body_text = msg.get("body", "")
            
            formatted_message = {
                "id": msg.get("mid"),
                "threadId": msg.get("tid"),
                "subject": msg.get("subject", "(No Subject)"),
                "from": self._format_address(msg.get("from")),
                "to": [self._format_address(addr) for addr in msg.get("to", [])],
                "cc": [self._format_address(addr) for addr in msg.get("cc", [])],
                "bcc": [self._format_address(addr) for addr in msg.get("bcc", [])],
                "date": msg.get("receivedDate"),
                "body": body_html or body_text,
                "bodyType": "html" if body_html else "text",
                "snippet": msg.get("snippet", ""),
                "isRead": msg.get("isRead", False),
                "hasAttachment": msg.get("hasAttachment", False),
                "attachments": msg.get("attachments", []),
                "provider": "yahoo"
            }
            
            logger.info(f"Retrieved Yahoo message: {message_id}")
            return formatted_message
            
        except Exception as e:
            logger.error(f"Failed to get Yahoo message {message_id}: {str(e)}")
            raise
    
    async def send_message(
        self,
        access_token: str,
        to: List[str],
        subject: str,
        body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        is_html: bool = True,
        attachments: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Send an email via Yahoo Mail
        
        Args:
            access_token: Valid Yahoo OAuth access token
            to: List of recipient email addresses
            subject: Email subject
            body: Email body content
            cc: Optional CC recipients
            bcc: Optional BCC recipients
            is_html: Whether body is HTML (default True)
            attachments: Optional list of attachments
            
        Returns:
            Dict with message ID and status
        """
        try:
            # Build message data
            message_data = {
                "to": [{"email": addr} for addr in to],
                "subject": subject,
                "body": body,
                "contentType": "text/html" if is_html else "text/plain"
            }
            
            if cc:
                message_data["cc"] = [{"email": addr} for addr in cc]
            if bcc:
                message_data["bcc"] = [{"email": addr} for addr in bcc]
            
            # Handle attachments if present
            if attachments:
                message_data["attachments"] = []
                for att in attachments:
                    message_data["attachments"].append({
                        "filename": att.get("filename", "attachment"),
                        "contentType": att.get("mimeType", "application/octet-stream"),
                        "content": att.get("data")  # Base64 encoded
                    })
            
            response = await self._make_request(
                "POST",
                "/messages",
                access_token,
                data=message_data
            )
            
            message_id = response.get("mid", response.get("messageId", ""))
            
            logger.info(f"Sent Yahoo email to {to}, message_id: {message_id}")
            
            return {
                "success": True,
                "message_id": message_id,
                "provider": "yahoo"
            }
            
        except Exception as e:
            logger.error(f"Failed to send Yahoo email: {str(e)}")
            raise
    
    async def mark_as_read(
        self,
        access_token: str,
        message_id: str
    ) -> bool:
        """Mark message as read"""
        try:
            await self._make_request(
                "POST",
                f"/messages/{message_id}/read",
                access_token,
                data={"isRead": True}
            )
            logger.info(f"Marked Yahoo message {message_id} as read")
            return True
        except Exception as e:
            logger.error(f"Failed to mark message as read: {str(e)}")
            return False
    
    async def mark_as_unread(
        self,
        access_token: str,
        message_id: str
    ) -> bool:
        """Mark message as unread"""
        try:
            await self._make_request(
                "POST",
                f"/messages/{message_id}/read",
                access_token,
                data={"isRead": False}
            )
            logger.info(f"Marked Yahoo message {message_id} as unread")
            return True
        except Exception as e:
            logger.error(f"Failed to mark message as unread: {str(e)}")
            return False
    
    async def delete_message(
        self,
        access_token: str,
        message_id: str
    ) -> bool:
        """Delete a message (move to trash)"""
        try:
            await self._make_request(
                "DELETE",
                f"/messages/{message_id}",
                access_token
            )
            logger.info(f"Deleted Yahoo message {message_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete message: {str(e)}")
            return False
    
    async def move_to_folder(
        self,
        access_token: str,
        message_id: str,
        folder_id: str
    ) -> bool:
        """Move message to specified folder"""
        try:
            await self._make_request(
                "POST",
                f"/messages/{message_id}/move",
                access_token,
                data={"fid": folder_id}
            )
            logger.info(f"Moved Yahoo message {message_id} to {folder_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to move message: {str(e)}")
            return False
    
    async def search_messages(
        self,
        access_token: str,
        query: str,
        count: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Search messages
        
        Args:
            access_token: Valid Yahoo OAuth access token
            query: Search query string
            count: Number of results
            offset: Offset for pagination
            
        Returns:
            Dict with matching messages
        """
        try:
            params = {
                "q": query,
                "count": count,
                "start": offset
            }
            
            response = await self._make_request(
                "GET",
                "/messages/search",
                access_token,
                params=params
            )
            
            messages = response.get("messages", [])
            
            # Transform to common format
            formatted_messages = []
            for msg in messages:
                formatted_messages.append({
                    "id": msg.get("mid"),
                    "subject": msg.get("subject", "(No Subject)"),
                    "from": self._format_address(msg.get("from")),
                    "date": msg.get("receivedDate"),
                    "snippet": msg.get("snippet", ""),
                    "provider": "yahoo"
                })
            
            return {
                "messages": formatted_messages,
                "total": response.get("total", len(formatted_messages))
            }
            
        except Exception as e:
            logger.error(f"Failed to search Yahoo messages: {str(e)}")
            raise
    
    async def create_draft(
        self,
        access_token: str,
        to: List[str],
        subject: str,
        body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        is_html: bool = True
    ) -> Dict[str, Any]:
        """
        Create a draft email
        
        Args:
            access_token: Valid Yahoo OAuth access token
            to: List of recipient email addresses
            subject: Email subject
            body: Email body content
            cc: Optional CC recipients
            bcc: Optional BCC recipients
            is_html: Whether body is HTML
            
        Returns:
            Dict with draft ID
        """
        try:
            draft_data = {
                "to": [{"email": addr} for addr in to],
                "subject": subject,
                "body": body,
                "contentType": "text/html" if is_html else "text/plain",
                "isDraft": True
            }
            
            if cc:
                draft_data["cc"] = [{"email": addr} for addr in cc]
            if bcc:
                draft_data["bcc"] = [{"email": addr} for addr in bcc]
            
            response = await self._make_request(
                "POST",
                "/drafts",
                access_token,
                data=draft_data
            )
            
            draft_id = response.get("mid", response.get("draftId", ""))
            
            logger.info(f"Created Yahoo draft: {draft_id}")
            
            return {
                "success": True,
                "draft_id": draft_id,
                "provider": "yahoo"
            }
            
        except Exception as e:
            logger.error(f"Failed to create Yahoo draft: {str(e)}")
            raise
    
    async def close(self):
        """Close HTTP client"""
        if self.http_client:
            await self.http_client.aclose()
            self.http_client = None


# Singleton instance
yahoo_mail_service = YahooMailService()
