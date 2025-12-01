from typing import Optional, List, Dict, Any
import base64
import aiosmtplib
import asyncio
import aiohttp
import json
import logging
import random
from datetime import datetime

logger = logging.getLogger(__name__)

class GmailService:
    def __init__(self):
        self.smtp_host = "smtp.gmail.com"
        self.smtp_port = 587
        self.base_url = "https://gmail.googleapis.com/gmail/v1"
        self._max_request_retries = 5
        self._initial_backoff_seconds = 1.0
        self._max_backoff_seconds = 16.0
        self._retryable_statuses = {429, 500, 502, 503, 504}
        self._max_concurrent_fetches = 5

    async def send_email_oauth(self, user_email: str, access_token: str, mime_message: bytes) -> str | None:
        auth_string = f"user={user_email}\x01auth=Bearer {access_token}\x01\x01"
        auth_b64 = base64.b64encode(auth_string.encode()).decode()
        smtp = aiosmtplib.SMTP(hostname=self.smtp_host, port=self.smtp_port, start_tls=True, timeout=30)
        await smtp.connect()
        code, msg = await smtp.execute_command("AUTH", "XOAUTH2", auth_b64)
        if code != 235:
            await smtp.quit()
            raise RuntimeError(f"Gmail auth failed: {code} {msg}")
        await smtp.sendmail(user_email, [user_email], mime_message)
        await smtp.quit()
        # Message ID extraction placeholder
        return None

    async def fetch_emails(self, access_token: str, folder: str = "INBOX", max_results: int = 50, page_token: str = None) -> Dict[str, Any]:
        """
        Fetch emails from Gmail using the API with pagination support
        
        Args:
            access_token: OAuth2 access token
            folder: Folder/label to fetch emails from
            max_results: Maximum number of results to return
            page_token: Token for pagination
            
        Returns:
            Dictionary with emails and next_page_token if available
        """
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Map folder names to Gmail labels
            folder_mapping = {
                "inbox": "INBOX",
                "sent": "SENT",
                "drafts": "DRAFT",
                "starred": "STARRED",
                "trash": "TRASH",
                "important": "IMPORTANT",
                "spam": "SPAM"
            }
            
            # Get proper label ID or use custom label directly
            label_id = folder_mapping.get(folder.lower(), folder.upper())
            
            async with aiohttp.ClientSession() as session:
                # First, get message list - sort by newest first
                list_url = f"{self.base_url}/users/me/messages"
                params = {
                    "labelIds": label_id,
                    "maxResults": max_results
                    # Removed newer_than filter to show all emails including old ones
                }
                
                if page_token:
                    params["pageToken"] = page_token
                
                data = await self._get_json_with_backoff(session, list_url, headers, params=params)
                if not data:
                    return {"emails": [], "next_page_token": None}

                messages = data.get("messages", [])
                next_page_token = data.get("nextPageToken")
                
                # Fetch detailed message data with parallel requests
                detailed_messages = []
                tasks = []
                semaphore = asyncio.Semaphore(self._max_concurrent_fetches)

                async def throttled_fetch(message_id: str):
                    async with semaphore:
                        return await self._fetch_message_details(session, message_id, headers)
                
                # Create tasks for parallel fetching
                for message in messages:
                    message_id = message.get('id')
                    if not message_id:
                        continue
                    task = asyncio.create_task(throttled_fetch(message_id))
                    tasks.append(task)
                
                # Process results as they complete
                if tasks:
                    # Wait for all tasks with timeout
                    completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Process completed tasks
                    for result in completed_tasks:
                        if isinstance(result, Exception):
                            logger.error(f"Error in fetch task: {result}")
                            continue
                        
                        if result:
                            detailed_messages.append(result)
                
                return {
                    "emails": detailed_messages,
                    "next_page_token": next_page_token
                }
                
        except Exception as e:
            logger.error(f"Error fetching Gmail emails: {e}")
            raise Exception(f"Failed to fetch Gmail emails: {str(e)}")

    async def _fetch_message_details(self, session: aiohttp.ClientSession, message_id: str, headers: Dict[str, str]) -> Dict[str, Any]:
        """Fetch details for a single message"""
        try:
            detail_url = f"{self.base_url}/users/me/messages/{message_id}"
            detail_data = await self._get_json_with_backoff(
                session,
                detail_url,
                headers,
                allow_statuses={404}
            )
            if not detail_data:
                return None
            return self._parse_gmail_message(detail_data)
                
        except Exception as e:
            logger.error(f"Error fetching message {message_id}: {e}")
            return None

    async def _get_json_with_backoff(
        self,
        session: aiohttp.ClientSession,
        url: str,
        headers: Dict[str, str],
        params: Optional[Dict[str, Any]] = None,
        allow_statuses: Optional[set[int]] = None
    ) -> Optional[Dict[str, Any]]:
        """Perform a GET request with exponential backoff for retryable Gmail errors."""
        backoff = self._initial_backoff_seconds
        for attempt in range(1, self._max_request_retries + 1):
            try:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    if allow_statuses and response.status in allow_statuses:
                        logger.info(
                            "Gmail request %s returned status %s (allowed)",
                            url,
                            response.status
                        )
                        return None

                    error_text = await response.text()
                    if response.status in self._retryable_statuses:
                        wait_time = min(backoff, self._max_backoff_seconds) + random.uniform(0, 0.5)
                        logger.warning(
                            "Gmail request %s failed with %s (%s/%s). Retrying in %.2fs",
                            url,
                            response.status,
                            attempt,
                            self._max_request_retries,
                            wait_time
                        )
                        await asyncio.sleep(wait_time)
                        backoff *= 2
                        continue

                    logger.error(
                        "Gmail request %s failed permanently: %s %s",
                        url,
                        response.status,
                        error_text
                    )
                    raise RuntimeError(f"Gmail API request failed: {response.status} {error_text}")
            except aiohttp.ClientError as client_error:
                wait_time = min(backoff, self._max_backoff_seconds) + random.uniform(0, 0.5)
                logger.warning(
                    "Gmail client error for %s (%s/%s): %s. Retrying in %.2fs",
                    url,
                    attempt,
                    self._max_request_retries,
                    client_error,
                    wait_time
                )
                await asyncio.sleep(wait_time)
                backoff *= 2
                continue

        raise RuntimeError(
            f"Gmail API request exceeded retry budget ({self._max_request_retries} attempts) for {url}"
        )
    
    def _parse_gmail_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Gmail API message into our format"""
        try:
            if not message:
                return None
                
            payload = message.get("payload", {})
            headers = payload.get("headers", [])
            
            # Extract headers
            subject = ""
            sender = ""
            recipient = ""
            date = ""
            message_id = ""
            cc = ""
            bcc = ""
            reply_to = ""
            custom_headers = {}
            
            for header in headers:
                name = header.get("name", "").lower()
                value = header.get("value", "")
                if name == "subject":
                    subject = value
                elif name == "from":
                    sender = value
                elif name == "to":
                    recipient = value
                elif name == "date":
                    date = value
                elif name == "message-id":
                    message_id = value
                elif name == "cc":
                    cc = value
                elif name == "bcc":
                    bcc = value
                elif name == "reply-to":
                    reply_to = value
                elif name.startswith("x-qumail-"):
                    custom_headers[name] = value
            
            # Extract body
            body_parts = self._extract_message_body_parts(payload)
            snippet = message.get("snippet", "")
            
            # Check labels for status
            label_ids = message.get("labelIds", [])
            is_read = "UNREAD" not in label_ids
            is_starred = "STARRED" in label_ids
            
            # Format datetime consistently for frontend
            timestamp = self._parse_email_date(date)
            
            # Extract attachment info
            attachments = self._extract_attachments(payload)
            
            # Process inline images in HTML content
            html_content = body_parts.get("html", "")
            inline_images = body_parts.get("inline_images", [])
            
            # Replace cid: references with data URLs for inline images
            if html_content and inline_images:
                html_content = self._process_inline_images(html_content, inline_images)
            
            return {
                "id": f"gmail_{message['id']}",
                "messageId": message_id,
                "threadId": message.get("threadId", ""),
                "sender": sender,
                "recipient": recipient, 
                "cc": cc,
                "bcc": bcc,
                "replyTo": reply_to,
                "subject": subject,
                "bodyText": body_parts.get("text", ""),
                "bodyHtml": html_content,
                "snippet": snippet,
                "timestamp": timestamp,
                "isRead": is_read,
                "isStarred": is_starred,
                "source": "gmail",
                "securityLevel": "standard",
                "labels": self._extract_labels(label_ids),
                "attachments": attachments,
                "hasAttachments": len(attachments) > 0,
                "inlineImages": len(inline_images) > 0,
                "customHeaders": custom_headers
            }
            
        except Exception as e:
            logger.error(f"Error parsing Gmail message: {e}")
            return None

    def _extract_message_body_parts(self, payload: Dict[str, Any]) -> Dict[str, str]:
        """Extract both HTML and plain text email bodies from Gmail payload"""
        result = {"text": "", "html": "", "inline_images": []}
        
        try:
            # Handle simple non-multipart messages
            if "body" in payload and "data" in payload["body"]:
                data = payload["body"]["data"]
                content = base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="ignore")
                
                if payload.get("mimeType") == "text/plain":
                    result["text"] = content
                    # Convert plain text to HTML with proper formatting
                    result["html"] = self._convert_text_to_html(content)
                elif payload.get("mimeType") == "text/html":
                    result["html"] = self._clean_html_content(content)
                    # Also provide plain text version
                    result["text"] = self._html_to_text(content)
                return result
            
            # Handle multipart messages recursively
            if "parts" in payload:
                self._process_parts(payload["parts"], result)
                
            # If we only have text, create HTML version
            if result["text"] and not result["html"]:
                result["html"] = self._convert_text_to_html(result["text"])
            # If we only have HTML, extract text version
            elif result["html"] and not result["text"]:
                result["text"] = self._html_to_text(result["html"])
                
            return result
            
        except Exception as e:
            logger.error(f"Error extracting message body parts: {e}")
            return result
            
    def _process_parts(self, parts: List[Dict[str, Any]], result: Dict[str, str]) -> None:
        """Process message parts recursively"""
        for part in parts:
            mime_type = part.get("mimeType", "")
            
            # Handle nested multipart
            if "parts" in part:
                self._process_parts(part["parts"], result)
                continue
                
            # Handle inline images
            if mime_type.startswith("image/") and "body" in part:
                headers = part.get("headers", [])
                content_id = None
                content_disposition = None
                
                for header in headers:
                    if header.get("name", "").lower() == "content-id":
                        content_id = header.get("value", "").strip("<>")
                    elif header.get("name", "").lower() == "content-disposition":
                        content_disposition = header.get("value", "")
                
                # Only process inline images
                if content_id or (content_disposition and "inline" in content_disposition.lower()):
                    if "data" in part["body"]:
                        image_data = part["body"]["data"]
                        result["inline_images"].append({
                            "contentId": content_id,
                            "mimeType": mime_type,
                            "data": image_data
                        })
                continue
                
            # Skip other attachments
            if mime_type.startswith("application/") or (mime_type.startswith("image/") and "filename" in part):
                continue
                
            # Extract text content when available
            if "body" in part and "data" in part["body"]:
                try:
                    data = part["body"]["data"]
                    content = base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="ignore")
                    
                    if mime_type == "text/plain":
                        # Append if we already have text content
                        if result["text"]:
                            result["text"] += "\n\n" + content
                        else:
                            result["text"] = content
                    elif mime_type == "text/html":
                        # Append if we already have HTML content
                        if result["html"]:
                            result["html"] += "<br><br>" + content
                        else:
                            result["html"] = self._clean_html_content(content)
                except Exception as e:
                    logger.error(f"Error processing part with mime type {mime_type}: {e}")

    def _extract_attachments(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract attachment information from message payload"""
        attachments = []
        
        try:
            # No parts means no attachments
            if "parts" not in payload:
                return attachments
                
            # Process parts recursively
            self._find_attachments(payload["parts"], attachments)
            
            return attachments
            
        except Exception as e:
            logger.error(f"Error extracting attachments: {e}")
            return []
    
    def _find_attachments(self, parts: List[Dict[str, Any]], attachments: List[Dict[str, Any]]) -> None:
        """Find attachments recursively in parts"""
        for part in parts:
            # Process nested parts
            if "parts" in part:
                self._find_attachments(part["parts"], attachments)
                
            # Check if this is an attachment
            if "filename" in part and part["filename"] and "body" in part:
                size = part["body"].get("size", 0)
                attachment_id = part["body"].get("attachmentId", "")
                
                # Only add if it has an attachment ID and size
                if attachment_id and size > 0:
                    attachments.append({
                        "id": attachment_id,
                        "filename": part["filename"],
                        "mimeType": part.get("mimeType", "application/octet-stream"),
                        "size": size
                    })
    
    def _parse_email_date(self, date_str: str) -> str:
        """Parse email date into consistent ISO format for frontend"""
        if not date_str:
            return ""
            
        try:
            from email.utils import parsedate_to_datetime
            import datetime
            
            # Parse RFC 2822 format
            dt = parsedate_to_datetime(date_str)
            # Convert to ISO format without microseconds
            return dt.replace(microsecond=0).isoformat()
        except Exception as e:
            logger.error(f"Error parsing date {date_str}: {e}")
            return date_str
    
    def _extract_labels(self, label_ids: List[str]) -> List[str]:
        """Convert Gmail label IDs to readable labels"""
        label_map = {
            "INBOX": "Inbox",
            "SENT": "Sent",
            "DRAFT": "Draft",
            "STARRED": "Starred",
            "TRASH": "Trash",
            "SPAM": "Spam",
            "IMPORTANT": "Important",
            "UNREAD": "Unread",
            "CATEGORY_PERSONAL": "Personal",
            "CATEGORY_SOCIAL": "Social",
            "CATEGORY_UPDATES": "Updates",
            "CATEGORY_FORUMS": "Forums",
            "CATEGORY_PROMOTIONS": "Promotions"
        }
        
        return [label_map.get(label_id, label_id) for label_id in label_ids if label_id in label_map]
    
    def _convert_text_to_html(self, text: str) -> str:
        """Convert plain text to HTML with proper formatting"""
        if not text:
            return ""
        
        import html
        # Escape HTML characters
        escaped = html.escape(text)
        
        # Convert line breaks to HTML
        html_content = escaped.replace('\n', '<br>')
        
        # Convert URLs to links
        import re
        url_pattern = r'(https?://[^\s<>"]+)'
        html_content = re.sub(url_pattern, r'<a href="\1" target="_blank">\1</a>', html_content)
        
        # Wrap in div for styling
        return f'<div style="white-space: pre-wrap; font-family: inherit;">{html_content}</div>'
    
    def _html_to_text(self, html: str) -> str:
        """Convert HTML to plain text"""
        if not html:
            return ""
        
        try:
            import re
            # Remove script and style elements
            html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
            html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
            
            # Convert common HTML elements to text equivalents
            html = re.sub(r'<br[^>]*>', '\n', html, flags=re.IGNORECASE)
            html = re.sub(r'<p[^>]*>', '\n\n', html, flags=re.IGNORECASE)
            html = re.sub(r'</p>', '', html, flags=re.IGNORECASE)
            html = re.sub(r'<div[^>]*>', '\n', html, flags=re.IGNORECASE)
            html = re.sub(r'</div>', '', html, flags=re.IGNORECASE)
            
            # Remove all other HTML tags
            text = re.sub(r'<[^>]+>', '', html)
            
            # Clean up whitespace
            text = re.sub(r'\n\s*\n', '\n\n', text)
            text = text.strip()
            
            return text
        except Exception as e:
            logger.error(f"Error converting HTML to text: {e}")
            return html
    
    def _clean_html_content(self, html: str) -> str:
        """Clean and sanitize HTML content"""
        if not html:
            return ""
        
        try:
            import re
            
            # Remove potentially dangerous elements
            html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
            html = re.sub(r'<object[^>]*>.*?</object>', '', html, flags=re.DOTALL | re.IGNORECASE)
            html = re.sub(r'<embed[^>]*>', '', html, flags=re.IGNORECASE)
            html = re.sub(r'<iframe[^>]*>.*?</iframe>', '', html, flags=re.DOTALL | re.IGNORECASE)
            
            # Remove dangerous attributes
            html = re.sub(r'\son\w+\s*=\s*["\'][^"\'>]*["\']', '', html, flags=re.IGNORECASE)
            html = re.sub(r'\sjavascript:', '', html, flags=re.IGNORECASE)
            
            # Ensure images have proper styling
            html = re.sub(r'<img([^>]*?)>', r'<img\1 style="max-width: 100%; height: auto;">', html, flags=re.IGNORECASE)
            
            return html
        except Exception as e:
            logger.error(f"Error cleaning HTML content: {e}")
            return html
    
    def _process_inline_images(self, html: str, inline_images: list) -> str:
        """Replace cid: references with data URLs for inline images"""
        if not html or not inline_images:
            return html
        
        try:
            import re
            
            for image in inline_images:
                content_id = image.get("contentId")
                mime_type = image.get("mimeType")
                data = image.get("data")
                
                if content_id and mime_type and data:
                    # Create data URL
                    data_url = f"data:{mime_type};base64,{data}"
                    
                    # Replace cid: references
                    cid_pattern = f'cid:{re.escape(content_id)}'
                    html = re.sub(cid_pattern, data_url, html, flags=re.IGNORECASE)
            
            return html
        except Exception as e:
            logger.error(f"Error processing inline images: {e}")
            return html

    async def get_gmail_folders(self, access_token: str) -> List[Dict[str, Any]]:
        """Get Gmail labels/folders with unread counts"""
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/users/me/labels"
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Failed to fetch Gmail labels: {response.status}, {error_text}")
                        raise Exception(f"Failed to fetch Gmail labels: {error_text}")
                    
                    data = await response.json()
                    labels = data.get("labels", [])
                    
                    # Define standard system folders we want to always include
                    standard_folders = [
                        {"id": "INBOX", "name": "Inbox", "type": "system"},
                        {"id": "SENT", "name": "Sent", "type": "system"},
                        {"id": "DRAFT", "name": "Drafts", "type": "system"},
                        {"id": "STARRED", "name": "Starred", "type": "system"},
                        {"id": "IMPORTANT", "name": "Important", "type": "system"},
                        {"id": "TRASH", "name": "Trash", "type": "system"},
                        {"id": "SPAM", "name": "Spam", "type": "system"}
                    ]
                    
                    # Map standard folders to IDs for quick lookup
                    standard_folder_map = {folder["id"]: folder for folder in standard_folders}
                    
                    # Process returned labels
                    folders = []
                    custom_folders = []
                    
                    for label in labels:
                        label_id = label["id"]
                        label_name = label["name"]
                        label_type = label["type"]
                        unread_count = label.get("messagesUnread", 0)
                        total_count = label.get("messagesTotal", 0)
                        
                        folder_info = {
                            "id": label_id,
                            "name": label_name,
                            "count": unread_count,
                            "total": total_count,
                            "type": label_type
                        }
                        
                        # If it's a standard system folder we want to include
                        if label_id in standard_folder_map:
                            # Update our standard folder info with real counts
                            standard_folder_map[label_id].update(folder_info)
                        elif label_type == "user":
                            # Add custom user folders separately
                            custom_folders.append(folder_info)
                    
                    # Add all standard folders first (with proper counts if they exist)
                    folders.extend([f for f in standard_folder_map.values() if f.get("total", 0) > 0 or f["id"] in ["INBOX", "SENT", "DRAFT"]])
                    
                    # Then add custom folders
                    folders.extend(custom_folders)
                    
                    return folders
                    
        except Exception as e:
            logger.error(f"Error fetching Gmail folders: {e}")
            raise Exception(f"Failed to fetch Gmail folders: {str(e)}")

    async def get_email_by_id(self, access_token: str, email_id: str) -> Dict[str, Any]:
        """Fetch single email by ID with full content"""
        try:
            # Strip 'gmail_' prefix if present
            if email_id.startswith("gmail_"):
                gmail_id = email_id[6:]
            else:
                gmail_id = email_id
                
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Fetch with format=full to get all message data
            async with aiohttp.ClientSession() as session:
                detail_url = f"{self.base_url}/users/me/messages/{gmail_id}?format=full"
                
                async with session.get(detail_url, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Failed to fetch email {gmail_id}: {response.status}, {error_text}")
                        raise Exception(f"Failed to fetch email: {error_text}")
                    
                    data = await response.json()
                    email_data = self._parse_gmail_message(data)
                    
                    # Mark as read if not already
                    if email_data and not email_data["isRead"]:
                        await self._mark_as_read(session, gmail_id, headers)
                    
                    return email_data
                    
        except Exception as e:
            logger.error(f"Error fetching email {email_id}: {e}")
            raise Exception(f"Failed to fetch email details: {str(e)}")
    
    async def mark_as_read(self, access_token: str, message_id: str) -> bool:
        """Public method to mark a message as read"""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            return await self._mark_as_read(session, message_id, headers)
    
    async def _mark_as_read(self, session: aiohttp.ClientSession, message_id: str, headers: Dict[str, str]) -> bool:
        """Mark a message as read by removing UNREAD label"""
        try:
            modify_url = f"{self.base_url}/users/me/messages/{message_id}/modify"
            data = {
                "removeLabelIds": ["UNREAD"]
            }
            
            async with session.post(modify_url, headers=headers, json=data) as response:
                return response.status == 200
                
        except Exception as e:
            logger.error(f"Failed to mark message {message_id} as read: {e}")
            return False
    
    async def get_attachment(self, access_token: str, message_id: str, attachment_id: str) -> Optional[Dict[str, Any]]:
        """Fetch attachment data for a message"""
        try:
            # Strip 'gmail_' prefix if present
            if message_id.startswith("gmail_"):
                gmail_id = message_id[6:]
            else:
                gmail_id = message_id
                
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/users/me/messages/{gmail_id}/attachments/{attachment_id}"
                
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Failed to fetch attachment {attachment_id}: {response.status}, {error_text}")
                        return None
                    
                    data = await response.json()
                    
                    # Attachment data is base64url encoded
                    attachment_data = data.get("data", "")
                    size = data.get("size", 0)
                    
                    return {
                        "id": attachment_id,
                        "data": attachment_data,
                        "size": size
                    }
                    
        except Exception as e:
            logger.error(f"Error fetching attachment {attachment_id}: {e}")
            return None

    async def send_email(self, access_token: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """Send email using Gmail API"""
        try:
            # First create MIME message
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            import base64
            
            # Create message container
            mime_message = MIMEMultipart('alternative')
            mime_message['Subject'] = message.get('subject', '(No subject)')
            mime_message['From'] = message.get('from', '')
            mime_message['To'] = message.get('to', '')
            
            # Add CC and BCC if provided
            if message.get('cc'):
                mime_message['Cc'] = message.get('cc')
            if message.get('bcc'):
                mime_message['Bcc'] = message.get('bcc')
            
            # Add custom headers if provided
            if message.get('headers'):
                for header_name, header_value in message.get('headers').items():
                    if header_value:
                        mime_message[header_name] = str(header_value)
                
            # Attach plain text and HTML parts
            if message.get('bodyText'):
                mime_message.attach(MIMEText(message.get('bodyText', ''), 'plain'))
            if message.get('bodyHtml'):
                mime_message.attach(MIMEText(message.get('bodyHtml', ''), 'html'))
            else:
                # If no HTML, convert plain text to simple HTML
                html_body = message.get('bodyText', '').replace('\n', '<br>')
                mime_message.attach(MIMEText(f'<div>{html_body}</div>', 'html'))
            
            # Convert message to base64url string
            encoded_message = base64.urlsafe_b64encode(mime_message.as_bytes()).decode()
            
            # Prepare API request
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            send_data = {
                "raw": encoded_message
            }
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/users/me/messages/send"
                
                async with session.post(url, headers=headers, json=send_data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Failed to send email: {response.status}, {error_text}")
                        raise Exception(f"Failed to send email: {error_text}")
                    
                    data = await response.json()
                    message_id = data.get("id", "")
                    thread_id = data.get("threadId", "")
                    
                    return {
                        "success": True,
                        "messageId": message_id,
                        "threadId": thread_id
                    }
                    
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            raise Exception(f"Failed to send email: {str(e)}")

gmail_service = GmailService()
