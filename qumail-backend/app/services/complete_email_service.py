"""
Complete Email Service with Real Quantum Encryption
Integrates KMS, encryption, Gmail, and database
"""
import logging
import uuid
import base64
import json
import re
import inspect
import html
import textwrap
from datetime import datetime
from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

from email.utils import parseaddr

from ..mongo_models import EmailDocument, EmailDirection, KeyUsageDocument
from ..mongo_repositories import EmailRepository, KeyUsageRepository, UserRepository
from .encryption.complete_encryption_service import complete_encryption_service
from .encryption.quantum_key_pool import quantum_key_pool
from .gmail_service import GmailService

logger = logging.getLogger(__name__)

class CompleteEmailService:
    """
    Complete email service with real quantum encryption
    - Encrypts emails before storing in Gmail
    - Stores encryption metadata in local database
    - Decrypts emails only in QuMail app
    """
    
    def __init__(self):
        self.encryption_service = complete_encryption_service
        self.key_pool = quantum_key_pool
        self.gmail_service = None  # Initialized per user
    
    async def send_encrypted_email(
        self,
        sender_email: str,
        sender_user_id: str,  # MongoDB user ID (string UUID)
        recipient_email: str,
        subject: str,
        body: str,
        security_level: int,
        cc: Optional[str] = None,
        bcc: Optional[str] = None,
        attachments: Optional[list] = None,
        db: AsyncIOMotorDatabase = None,
        gmail_credentials: Dict = None
    ) -> Dict[str, Any]:
        """
        Send email with specified security level encryption
        
        Flow:
        1. Encrypt subject and body with chosen security level
        2. Store encryption metadata in local database
        3. Send encrypted content to Gmail
        4. Gmail stores only encrypted data
        """
        try:
            logger.info(f"Sending encrypted email with security level {security_level}")
            
            # Prepare message for encryption
            message_data = {
                'subject': subject,
                'body': body,
                'from': sender_email,
                'to': recipient_email,
                'cc': cc,
                'bcc': bcc,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            message_json = json.dumps(message_data)
            # Encryption functions expect STRING not bytes
            
            # Encrypt based on security level
            if security_level == 1:
                encryption_result = await self.encryption_service.encrypt_level_1_otp(message_json, sender_email)
            elif security_level == 2:
                encryption_result = await self.encryption_service.encrypt_level_2_aes(message_json, sender_email)
            elif security_level == 3:
                encryption_result = await self.encryption_service.encrypt_level_3_pqc(message_json, sender_email)
            elif security_level == 4:
                encryption_result = await self.encryption_service.encrypt_level_4_standard(message_json, sender_email)
            else:
                raise ValueError(f"Invalid security level: {security_level}")
            
            # Generate unique flow ID
            flow_id = encryption_result['metadata'].get('flow_id', str(uuid.uuid4()))
            
            # Extract metadata for storage (tested functions use nested metadata)
            metadata = encryption_result.get('metadata', {})
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except json.JSONDecodeError:
                    metadata = {'raw_metadata': metadata}
            else:
                metadata = dict(metadata)

            encrypted_data = encryption_result.get('encrypted_content', encryption_result.get('encrypted_data'))
            
            # Create email record in database with encryption metadata
            # Store auth_tag in metadata so it's available during decryption
            if encryption_result.get('auth_tag'):
                metadata['auth_tag'] = encryption_result['auth_tag']
            elif encryption_result.get('signature'):
                # Fallback for legacy/RSA
                metadata['signature'] = encryption_result['signature']
            
            email_repo = EmailRepository(db)
            email_doc = EmailDocument(
                flow_id=flow_id,
                user_id=sender_user_id,  # MongoDB user ID (string UUID)
                sender_email=sender_email,
                receiver_email=recipient_email,
                subject=f"[ENCRYPTED-L{security_level}] {subject[:50]}...",  # Encrypted subject indicator
                body_encrypted=encrypted_data,
                security_level=security_level,
                direction=EmailDirection.SENT,
                timestamp=datetime.utcnow(),
                is_read=False,
                is_starred=False,
                is_suspicious=False,
                # Store encryption metadata
                encryption_key_id=metadata.get('key_id', metadata.get('key_ids', {}).get('km1', '')),
                encryption_algorithm=encryption_result.get('algorithm'),
                encryption_iv=metadata.get('nonce'),  # 'nonce' in tested functions
                encryption_auth_tag=encryption_result.get('auth_tag') or encryption_result.get('signature'),  # Prefer auth_tag
                encryption_metadata=metadata  # Stored as structured metadata for quick access
            )
            
            email = await email_repo.create(email_doc)
            
            # Record key usage
            key_usage_repo = KeyUsageRepository(db)
            key_usage_doc = KeyUsageDocument(
                email_id=email.flow_id,
                key_id=metadata.get('key_id', metadata.get('key_ids', {}).get('km1', '')),
                algorithm=encryption_result.get('algorithm'),
                key_size=len(message_json),
                entropy_score=metadata.get('entropy', 0.0),
                source_kme='KME1',
                timestamp=datetime.utcnow()
            )
            
            await key_usage_repo.create(key_usage_doc)
            
            # Process and encrypt attachments if provided
            attachment_ids = []
            if attachments:
                from ..mongo_repositories import AttachmentRepository
                attachment_repo = AttachmentRepository(db)
                
                logger.info(f"Processing {len(attachments)} attachment(s) for encryption")
                
                for idx, att_data in enumerate(attachments):
                    # Encrypt attachment content - use Level 4 for attachments to conserve quantum keys
                    att_content = att_data.get('content', '')
                    if att_content:
                        try:
                            # Always use Level 4 (RSA+AES) for attachments to avoid exhausting quantum keys
                            logger.info(f"Encrypting attachment {idx+1}/{len(attachments)}: {att_data.get('filename', 'unknown')}")
                            att_encrypted = await self.encryption_service.encrypt_level_4_standard(att_content, sender_email)
                            
                            encrypted_att_content = att_encrypted.get('encrypted_content', att_encrypted.get('encrypted_data'))
                            
                            # Store encrypted attachment
                            from ..mongo_models import AttachmentDocument
                            att_doc = AttachmentDocument(
                                email_id=email.id,
                                filename=att_data.get('filename', 'attachment'),
                                content_type=att_data.get('mimeType', 'application/octet-stream'),
                                size=len(att_content),
                                encrypted_data=encrypted_att_content if isinstance(encrypted_att_content, str) else base64.b64encode(encrypted_att_content).decode('utf-8')
                            )
                            
                            saved_att = await attachment_repo.create(att_doc)
                            attachment_ids.append(saved_att.id)
                            logger.info(f"✓ Attachment encrypted and stored: {att_doc.filename} ({att_doc.size} bytes)")
                        except Exception as att_error:
                            logger.error(f"Failed to encrypt attachment {att_data.get('filename', 'unknown')}: {att_error}")
                            # Continue with other attachments even if one fails
            
            # Send encrypted email via Gmail
            if gmail_credentials:
                try:
                    from .gmail_service import gmail_service
                    
                    # Prepare encrypted email for Gmail
                    encrypted_subject = f"🔐 QuMail Encrypted L{security_level}"
                    key_id = metadata.get('key_id') or metadata.get('key_ids', {}).get('km1') or encryption_result.get('key_id', 'unknown-key')
                    ciphertext_b64 = ''
                    if encrypted_data:
                        if isinstance(encrypted_data, bytes):
                            ciphertext_b64 = base64.b64encode(encrypted_data).decode('utf-8')
                        else:
                            ciphertext_b64 = str(encrypted_data)

                    encrypted_body_html = self._build_gmail_html_template(
                        security_level=security_level,
                        algorithm=encryption_result.get('algorithm', 'unknown'),
                        key_id=key_id,
                        flow_id=flow_id,
                        sender_email=sender_email,
                        recipient_email=recipient_email,
                        ciphertext=ciphertext_b64,
                        timestamp=message_data['timestamp']
                    )

                    encrypted_body_text = self._build_gmail_text_template(
                        security_level=security_level,
                        algorithm=encryption_result.get('algorithm', 'unknown'),
                        key_id=key_id,
                        flow_id=flow_id,
                        ciphertext=ciphertext_b64
                    )
                    
                    # Get a valid access token (automatically refreshes if expired)
                    from .gmail_oauth import oauth_service
                    access_token = await oauth_service.get_valid_access_token(sender_email, db)
                    
                    # Prepare message for Gmail API
                    message = {
                        'from': sender_email,
                        'to': recipient_email,
                        'subject': encrypted_subject,
                        'bodyText': encrypted_body_text,
                        'bodyHtml': encrypted_body_html,
                        'cc': cc,
                        'bcc': bcc,
                        'headers': {
                            'X-QuMail-Flow-ID': flow_id,
                            'X-QuMail-Key-ID': key_id,
                            'X-QuMail-Algorithm': encryption_result.get('algorithm', 'unknown'),
                            'X-QuMail-Security-Level': str(security_level),
                            'X-QuMail-Auth-Tag': metadata.get('auth_tag', ''),
                            'X-QuMail-Nonce': metadata.get('nonce', '')
                        }
                    }
                    
                    # Send via Gmail
                    result = await gmail_service.send_email(access_token, message)
                    gmail_message_id = result.get('messageId')
                    
                    # Store Gmail message ID
                    await email_repo.update(email.id, {"gmail_message_id": gmail_message_id})
                    email.gmail_message_id = gmail_message_id
                    
                    logger.info(f"Encrypted email sent via Gmail: {gmail_message_id}")
                    
                except Exception as gmail_error:
                    logger.error(f"Gmail send failed: {gmail_error}")
                    # Continue even if Gmail fails - email is stored locally
            
            logger.info(f"Encrypted email created successfully: {flow_id}")
            
            return {
                'success': True,
                'email_id': email.flow_id,
                'flow_id': flow_id,
                'encryption_details': {
                    'algorithm': encryption_result.get('algorithm'),
                    'security_level': security_level,
                    'key_id': metadata.get('key_id', metadata.get('key_ids', {}).get('km1', '')),
                    'encrypted_size': len(encrypted_data)
                },
                'gmail_message_id': email.gmail_message_id,
                'timestamp': email.timestamp.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error sending encrypted email: {e}")
            raise Exception(f"Failed to send encrypted email: {e}")
    
    def _build_gmail_html_template(
        self,
        security_level: int,
        algorithm: str,
        key_id: str,
        flow_id: str,
        sender_email: str,
        recipient_email: str,
        ciphertext: str,
        timestamp: str
    ) -> str:
        """Generate Gmail-friendly HTML mirroring the secure branding."""
        level_titles = {
            1: "Quantum OTP (One-Time Pad)",
            2: "AES-256-GCM Quantum-Enhanced",
            3: "Post-Quantum Kyber + Dilithium",
            4: "Hybrid RSA-4096 + AES"
        }
        level_title = level_titles.get(security_level, "Quantum Encryption")
        wrapped_lines = textwrap.wrap(ciphertext or 'Ciphertext unavailable', 80)
        ciphertext_wrapped = '<br>'.join(html.escape(line) for line in wrapped_lines)

        return f"""<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background-color:#050505;font-family:'Segoe UI',Arial,sans-serif;color:#f0f0f0;">
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color:#050505;padding:24px 0;">
<tr>
<td>
<table role="presentation" align="center" width="620" cellspacing="0" cellpadding="0" style="background-color:#111;border:1px solid #ff1f3d;border-radius:10px;padding:32px;box-shadow:0 12px 40px rgba(0,0,0,0.65);">
<tr>
<td style="text-align:center;padding-bottom:16px;">
<div style="font-size:26px;font-weight:600;">🔐 QUANTUM-ENCRYPTED EMAIL 🔐</div>
<div style="margin-top:12px;display:inline-block;padding:6px 14px;border-radius:999px;background:#ff1f3d;color:#fff;font-size:14px;font-weight:600;">Security Level {security_level}</div>
<div style="margin-top:6px;color:#f7c948;font-size:15px;">{html.escape(level_title)}</div>
</td>
</tr>
<tr>
<td style="background:#1a1a1a;border:1px solid #ff1f3d;border-radius:8px;padding:18px;color:#ffd6d6;font-size:14px;font-weight:500;">
⚠️ ENCRYPTED MESSAGE — Only QuMail can decrypt this content. Unauthorized attempts are logged.
</td>
</tr>
<tr>
<td style="padding-top:18px;">
<table width="100%" cellspacing="0" cellpadding="0" style="background:#0f1c1c;border:1px solid #1c5b5b;border-radius:8px;padding:18px;color:#e8feff;font-size:14px;">
<tr><td style="font-weight:600;text-transform:uppercase;letter-spacing:0.08em;color:#7fffd4;padding-bottom:10px;">Encryption Details</td></tr>
<tr><td><strong>Algorithm:</strong> {html.escape(algorithm)}</td></tr>
<tr><td><strong>Flow ID:</strong> {html.escape(flow_id)}</td></tr>
<tr><td><strong>Key ID:</strong> {html.escape(key_id)}</td></tr>
<tr><td><strong>From:</strong> {html.escape(sender_email)}<br><strong>To:</strong> {html.escape(recipient_email)}</td></tr>
<tr><td><strong>Timestamp:</strong> {html.escape(timestamp)}</td></tr>
<tr><td><strong>Status:</strong> <span style="color:#19ff62;font-weight:600;">● ENCRYPTED</span></td></tr>
</table>
</td>
</tr>
<tr>
<td style="padding-top:18px;">
<div style="text-align:center;font-size:14px;color:#ff305a;margin-bottom:10px;font-weight:600;">──── ENCRYPTED CONTENT (BASE64 CIPHERTEXT) ────</div>
<div style="background:#140202;border:1px solid #ff1f3d;border-radius:8px;padding:20px;color:#ffb3b3;font-family:'Lucida Console',Menlo,monospace;font-size:13px;line-height:1.4;word-break:break-all;">
{ciphertext_wrapped}
</div>
</td>
</tr>
<tr>
<td style="padding-top:18px;">
<table width="100%" cellspacing="0" cellpadding="0" style="background:#200000;border:1px solid #ff1f3d;border-radius:8px;padding:16px;color:#ffdddd;font-size:13px;">
<tr><td style="font-weight:600;">⚠️ SECURITY WARNING</td></tr>
<tr><td style="padding-top:6px;">• Do NOT attempt to decrypt this message manually.<br>• Content protected by quantum key distribution (QKD).<br>• Only QuMail application can decrypt this message.<br>• Unauthorized attempts will be logged.</td></tr>
</table>
</td>
</tr>
<tr>
<td style="padding-top:22px;text-align:center;font-size:13px;color:#a0a0a0;">
<div>To read this encrypted message:</div>
<a href="https://qumail.app/download" style="display:inline-block;margin-top:10px;padding:10px 26px;background:#ff1f3d;color:#fff;border-radius:999px;text-decoration:none;font-weight:600;">Download QuMail Application</a>
</td>
</tr>
<tr>
<td style="padding-top:16px;text-align:center;font-size:12px;color:#7c7c7c;">
Protected by Quantum Key Distribution | End-to-End Encrypted
</td>
</tr>
</table>
</td>
</tr>
</table>
</body>
</html>"""

    def _build_gmail_text_template(
        self,
        security_level: int,
        algorithm: str,
        key_id: str,
        flow_id: str,
        ciphertext: str
    ) -> str:
        """Plain-text fallback for email clients."""
        header = f"QUANTUM-ENCRYPTED EMAIL (Level {security_level})\n"
        details = (
            f"Algorithm: {algorithm}\n"
            f"Key ID: {key_id}\n"
            f"Flow ID: {flow_id}\n"
            "Status: ENCRYPTED\n"
            "--------------------------------------------\n"
        )
        warning = (
            "SECURITY WARNING:\n"
            "- Only QuMail can decrypt this message.\n"
            "- Unauthorized attempts are logged.\n"
        )
        ciphertext_formatted = textwrap.fill(ciphertext or 'Ciphertext unavailable', width=80)
        return (
            f"{header}\n"
            "This message is protected by quantum cryptography.\n\n"
            f"{details}\n"
            "ENCRYPTED CONTENT (BASE64):\n"
            f"{ciphertext_formatted}\n\n"
            f"{warning}\n"
            "Download QuMail to decrypt: https://qumail.app/download"
        )
    
    async def receive_and_decrypt_email(
        self,
        email_id: str,  # UUID string
        db: AsyncIOMotorDatabase
    ) -> Dict[str, Any]:
        """
        Receive and decrypt email - ONLY in QuMail app
        
        Flow:
        1. Fetch email from database
        2. Check if decrypted content is cached
        3. If cached, return immediately (no KME calls)
        4. If not cached, decrypt and store cache
        5. Return plaintext ONLY to QuMail app
        """
        try:
            # Fetch email from database
            email_repo = EmailRepository(db)
            email = await email_repo.find_by_id(email_id)
            
            if not email:
                raise Exception(f"Email {email_id} not found")
            
            # Check if decrypted content is already cached
            if email.decrypted_body:
                logger.info(f"✓ Email {email_id} already decrypted - returning cached content (no KME calls)")
                
                # Parse cached decrypted message
                try:
                    message_data = json.loads(email.decrypted_body)
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse cached content for {email_id}, will re-decrypt")
                    message_data = None
                
                if message_data:
                    # Mark as read
                    await email_repo.mark_as_read(email.id)
                    
                    # Get cached attachments
                    from ..mongo_repositories import AttachmentRepository
                    attachment_repo = AttachmentRepository(db)
                    attachments = await attachment_repo.list_by_email(email.id)
                    
                    cached_attachments = []
                    for att in attachments:
                        # Check if attachment is already decrypted
                        if att.decrypted_content:
                            content = att.decrypted_content
                        else:
                            # Not decrypted yet (legacy cache), decrypt now
                            try:
                                logger.info(f"Decrypting attachment for cached email: {att.filename}")
                                att_metadata = {'flow_id': email.flow_id}
                                decrypted_att = await self.encryption_service.decrypt_level_4_standard(
                                    att.encrypted_data, att_metadata, email.receiver_email
                                )
                                content = decrypted_att.decode('utf-8') if isinstance(decrypted_att, bytes) else decrypted_att
                                
                                # Save to DB
                                await attachment_repo.update(att.id, {"decrypted_content": content})
                                logger.info(f"✓ Cached decrypted content for attachment {att.filename}")
                            except Exception as e:
                                logger.error(f"Failed to decrypt attachment {att.filename}: {e}")
                                content = None

                        cached_attachments.append({
                            'id': att.id,
                            'filename': att.filename,
                            'content': content,
                            'mimeType': att.content_type,
                            'size': att.size
                        })
                    
                    return {
                        'success': True,
                        'email_id': email.id,
                        'flow_id': email.flow_id,
                        'subject': message_data.get('subject'),
                        'body': message_data.get('body'),
                        'from': message_data.get('from'),
                        'to': message_data.get('to'),
                        'cc': message_data.get('cc'),
                        'bcc': message_data.get('bcc'),
                        'timestamp': message_data.get('timestamp'),
                        'security_level': email.security_level,
                        'algorithm': email.encryption_algorithm,
                        'decrypted_at': datetime.utcnow().isoformat(),
                        'attachments': cached_attachments,
                        'from_cache': True
                    }
            
            logger.info(f"Decrypting email {email_id} with security level {email.security_level} (no cache, will call KME)")
            
            # Build metadata dict from stored fields
            metadata = {
                'flow_id': email.flow_id,
                'key_id': email.encryption_key_id,
                'algorithm': email.encryption_algorithm,
                'nonce': email.encryption_iv,
                'auth_tag': email.encryption_auth_tag
            }
            
            # Add any extra metadata from JSON field (handle legacy JSON strings)
            extra_metadata = email.encryption_metadata
            if isinstance(extra_metadata, str):
                try:
                    extra_metadata = json.loads(extra_metadata)
                except json.JSONDecodeError:
                    extra_metadata = {'raw_metadata': extra_metadata}

            if extra_metadata:
                metadata.update(extra_metadata)
            
            # Decrypt based on security level using TESTED functions
            if email.security_level == 1:
                decrypted_bytes = await self.encryption_service.decrypt_level_1_otp(
                    email.body_encrypted,
                    metadata,
                    email.receiver_email
                )
            elif email.security_level == 2:
                decrypted_bytes = await self.encryption_service.decrypt_level_2_aes(
                    email.body_encrypted,
                    metadata,
                    email.receiver_email
                )
            elif email.security_level == 3:
                decrypted_bytes = await self.encryption_service.decrypt_level_3_pqc(
                    email.body_encrypted,
                    metadata,
                    email.receiver_email
                )
            elif email.security_level == 4:
                decrypted_bytes = await self.encryption_service.decrypt_level_4_standard(
                    email.body_encrypted,
                    metadata,
                    email.receiver_email
                )
            else:
                raise ValueError(f"Invalid security level: {email.security_level}")
            
            # Parse decrypted message
            decrypted_json = decrypted_bytes.decode('utf-8')
            message_data = json.loads(decrypted_json)
            
            # Decrypt attachments if any
            from ..mongo_repositories import AttachmentRepository
            attachment_repo = AttachmentRepository(db)
            attachments = await attachment_repo.list_by_email(email.id)
            
            decrypted_attachments = []
            for att in attachments:
                try:
                    # Check if already decrypted
                    if att.decrypted_content:
                        decrypted_content = att.decrypted_content
                        logger.info(f"✓ Using cached decrypted content for attachment {att.filename}")
                    else:
                        # Attachments are always encrypted with Level 4 (to conserve quantum keys)
                        att_metadata = {'flow_id': email.flow_id}
                        
                        logger.info(f"Decrypting attachment: {att.filename}")
                        decrypted_att = await self.encryption_service.decrypt_level_4_standard(
                            att.encrypted_data, att_metadata, email.receiver_email
                        )
                        
                        decrypted_content = decrypted_att.decode('utf-8') if isinstance(decrypted_att, bytes) else decrypted_att
                        
                        # Cache the decrypted content
                        await attachment_repo.update(att.id, {"decrypted_content": decrypted_content})
                        logger.info(f"✓ Cached decrypted content for attachment {att.filename}")
                    
                    decrypted_attachments.append({
                        'id': att.id,
                        'filename': att.filename,
                        'content': decrypted_content,
                        'mimeType': att.content_type,
                        'size': att.size
                    })
                    logger.info(f"✓ Decrypted attachment: {att.filename}")
                except Exception as att_error:
                    logger.error(f"Failed to decrypt attachment {att.filename}: {att_error}")
            
            # Cache the decrypted content for future use (no need to call KME again)
            email.decrypted_body = decrypted_json
            await email_repo.update(email.id, {"decrypted_body": decrypted_json})
            logger.info(f"✓ Cached decrypted content for email {email_id} - future views will be instant")
            
            # Mark key as consumed in shared pool (permanently remove)
            # This ensures true OTP security (key used once) while allowing retry if decryption fails before caching
            if email.encryption_key_id and email.security_level in [1, 2, 3]:
                try:
                    from .km_client_init import get_optimized_km_clients
                    km1_client, _ = get_optimized_km_clients()
                    await km1_client.mark_key_consumed(email.encryption_key_id)
                    logger.info(f"✓ Key {email.encryption_key_id} marked as consumed in shared pool")
                except Exception as e:
                    logger.error(f"Failed to mark key {email.encryption_key_id} as consumed: {e}")
            
            # Mark as read
            await email_repo.mark_as_read(email.id)
            
            logger.info(f"Email {email_id} decrypted successfully with {len(decrypted_attachments)} attachments")
            
            return {
                'success': True,
                'email_id': email.id,
                'flow_id': email.flow_id,
                'subject': message_data.get('subject'),
                'body': message_data.get('body'),
                'from': message_data.get('from'),
                'to': message_data.get('to'),
                'cc': message_data.get('cc'),
                'bcc': message_data.get('bcc'),
                'timestamp': message_data.get('timestamp'),
                'security_level': email.security_level,
                'algorithm': email.encryption_algorithm,
                'decrypted_at': datetime.utcnow().isoformat(),
                'attachments': decrypted_attachments,
                'from_cache': False
            }
            
        except Exception as e:
            logger.error(f"Error decrypting email {email_id}: {e}")
            raise Exception(f"Failed to decrypt email: {e}")
    
    async def get_encrypted_email_list(
        self,
        user_email: str,
        folder: str,
        db: AsyncIOMotorDatabase
    ) -> list:
        """
        Get list of encrypted emails (metadata only, no decryption)
        """
        try:
            # Determine direction based on folder
            if folder == 'sent':
                direction = EmailDirection.SENT
                email_filter = Email.sender_email == user_email
            else:  # inbox
                direction = EmailDirection.RECEIVED
                email_filter = Email.receiver_email == user_email
            
            # Query emails
            email_repo = EmailRepository(db)
            emails = await email_repo.list_by_user(user_email, direction, limit=100)
            
            # Return metadata only (no decryption)
            email_list = []
            for email in emails:
                metadata = email.encryption_metadata or {}
                if isinstance(metadata, str):
                    try:
                        metadata = json.loads(metadata)
                    except json.JSONDecodeError:
                        metadata = {'raw_metadata': metadata}

                is_encrypted = email.security_level in (1, 2, 3, 4)
                snippet = metadata.get('snippet') or ''
                if not snippet and email.body_encrypted:
                    snippet = (email.body_encrypted[:160] + '...') if len(email.body_encrypted) > 160 else email.body_encrypted
                if is_encrypted and email.encryption_algorithm:
                    snippet = f"Encrypted with {email.encryption_algorithm}"

                email_list.append({
                    'id': email.flow_id,
                    'flow_id': email.flow_id,
                    'from': email.sender_email,
                    'to': email.receiver_email,
                    'subject': email.subject,
                    'snippet': snippet,
                    'timestamp': email.timestamp.isoformat(),
                    'read': email.is_read,
                    'security_level': email.security_level,
                    'encrypted': is_encrypted,
                    'source': metadata.get('source', 'qumail' if is_encrypted else 'gmail'),
                    'labels': metadata.get('labels', []),
                    'gmailMessageId': email.gmail_message_id,
                    'hasAttachments': metadata.get('hasAttachments', False),
                    'senderDisplay': metadata.get('senderDisplay', email.sender_email),
                    'receiverDisplay': metadata.get('receiverDisplay', email.receiver_email)
                })

            return email_list
            
        except Exception as e:
            logger.error(f"Error getting email list: {e}")
            raise
    
    async def sync_gmail_encrypted_emails(
        self,
        user_email: str,
        gmail_credentials: Dict,
        db: AsyncIOMotorDatabase
    ) -> Dict[str, Any]:
        """
        Sync encrypted emails from Gmail
        - Fetch encrypted emails from Gmail
        - Store in local database with encryption metadata
        """
        try:
            from .gmail_service import gmail_service
            from .gmail_oauth import oauth_service
            
            # Get a valid access token (automatically refreshes if expired)
            access_token = await oauth_service.get_valid_access_token(user_email, db)
            
            # Fetch emails from Gmail using valid access token
            gmail_result = await gmail_service.fetch_emails(access_token, folder="INBOX", max_results=50)
            gmail_messages = gmail_result.get("emails", [])

            synced_total = 0
            encrypted_synced = 0

            # Resolve current user to associate stored messages
            user_repo = UserRepository(db)
            user = await user_repo.find_by_email(user_email)
            if not user:
                raise ValueError(f"User {user_email} not found in database")

            email_repo = EmailRepository(db)
            
            for gmail_msg in gmail_messages:
                gmail_message_id = gmail_msg.get('id')
                if not gmail_message_id:
                    continue

                # Skip if already stored locally
                existing_email = await email_repo.find_by_gmail_id(gmail_message_id)
                if existing_email:
                    continue

                subject = gmail_msg.get('subject') or '(No subject)'
                body_html = gmail_msg.get('bodyHtml')
                body_text = gmail_msg.get('bodyText') or gmail_msg.get('snippet') or ''
                if not body_text and body_html:
                    # Basic HTML to text fallback
                    body_text = re.sub('<[^<]+?>', '', body_html)

                sender_display = gmail_msg.get('sender') or gmail_msg.get('from') or gmail_msg.get('from_email') or ''
                recipient_display = gmail_msg.get('recipient') or user_email
                sender_name, sender_email = parseaddr(sender_display)
                receiver_name, receiver_email = parseaddr(recipient_display)
                if not sender_email:
                    sender_email = sender_display
                if not receiver_email:
                    receiver_email = user_email

                metadata = {
                    'source': 'gmail',
                    'labels': gmail_msg.get('labels', []),
                    'threadId': gmail_msg.get('threadId'),
                    'messageIdHeader': gmail_msg.get('messageId'),
                    'snippet': gmail_msg.get('snippet'),
                    'hasAttachments': gmail_msg.get('hasAttachments', False),
                    'bodyText': body_text,
                    'bodyHtml': body_html,
                    'attachments': gmail_msg.get('attachments', []),
                    'gmailMessageId': gmail_message_id
                }
                if sender_name:
                    metadata['senderName'] = sender_name
                metadata['senderDisplay'] = sender_display
                if receiver_name:
                    metadata['receiverName'] = receiver_name
                metadata['receiverDisplay'] = recipient_display

                is_qumail_encrypted = '[QuMail Encrypted' in subject
                security_level = 0
                encryption_algorithm = None
                encryption_key_id = None
                flow_id = None

                if is_qumail_encrypted:
                    encrypted_synced += 1
                    
                    # Try to get metadata from headers first (more reliable)
                    custom_headers = gmail_msg.get('customHeaders', {})
                    
                    if 'x-qumail-security-level' in custom_headers:
                        try:
                            security_level = int(custom_headers['x-qumail-security-level'])
                        except ValueError:
                            security_level = 1
                    else:
                        # Fallback to subject parsing
                        level_match = re.search(r'L(\d)', subject)
                        if level_match:
                            security_level = int(level_match.group(1))
                        else:
                            security_level = 1
                            
                    if 'x-qumail-algorithm' in custom_headers:
                        encryption_algorithm = custom_headers['x-qumail-algorithm']
                    else:
                        # Fallback to body parsing
                        algorithm_match = re.search(r'Algorithm:\s*(.+)', body_text)
                        if algorithm_match:
                            encryption_algorithm = algorithm_match.group(1).strip()
                            
                    if 'x-qumail-key-id' in custom_headers:
                        encryption_key_id = custom_headers['x-qumail-key-id']
                    else:
                        # Fallback to body parsing
                        key_match = re.search(r'Key ID:\s*(.+)', body_text)
                        if key_match:
                            encryption_key_id = key_match.group(1).strip()
                            
                    if 'x-qumail-flow-id' in custom_headers:
                        flow_id = custom_headers['x-qumail-flow-id']
                    else:
                        # Fallback to body parsing
                        flow_match = re.search(r'Flow ID:\s*(.+)', body_text)
                        if flow_match:
                            flow_id = flow_match.group(1).strip()
                            
                    # Store extra header metadata if available
                    if 'x-qumail-auth-tag' in custom_headers:
                        metadata['auth_tag'] = custom_headers['x-qumail-auth-tag']
                    if 'x-qumail-nonce' in custom_headers:
                        metadata['nonce'] = custom_headers['x-qumail-nonce']
                        
                    metadata['sync_type'] = 'qumail_encrypted'
                else:
                    metadata['sync_type'] = 'gmail_plain'

                if not flow_id:
                    flow_id = f"gmail:{gmail_message_id}"

                timestamp_str = gmail_msg.get('timestamp')
                timestamp = datetime.utcnow()
                if timestamp_str:
                    try:
                        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    except Exception:
                        pass

                body_content = body_html or body_text or ''

                email_doc = EmailDocument(
                    flow_id=flow_id,
                    user_id=str(user.id),
                    sender_email=sender_email,
                    receiver_email=receiver_email,
                    subject=subject,
                    body_encrypted=body_content,
                    security_level=security_level,
                    direction=EmailDirection.RECEIVED,
                    timestamp=timestamp,
                    is_read=gmail_msg.get('isRead', False),
                    is_starred=gmail_msg.get('isStarred', False),
                    is_suspicious=False,
                    gmail_message_id=gmail_message_id,
                    encryption_key_id=encryption_key_id,
                    encryption_algorithm=encryption_algorithm,
                    encryption_iv=None,
                    encryption_auth_tag=None,
                    encryption_metadata=metadata
                )

                await email_repo.create(email_doc)
                synced_total += 1

            return {
                'success': True,
                'synced_count': synced_total,
                'encrypted_synced': encrypted_synced,
                'total_messages': len(gmail_messages)
            }
            
        except Exception as e:
            logger.error(f"Error syncing Gmail emails: {e}")
            raise

# Global complete email service instance
complete_email_service = CompleteEmailService()
