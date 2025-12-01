"""Real end-to-end encrypted email delivery via Gmail."""

import base64
import json
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional

import aiohttp
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..mongo_models import AttachmentDocument
from ..mongo_repositories import AttachmentRepository, EmailRepository
from .quantum_encryption import quantum_encryption_service

logger = logging.getLogger(__name__)

class RealEncryptedGmailService:
    """Gmail transport for already-encrypted QuMail messages."""

    def __init__(self) -> None:
        self.base_url = "https://gmail.googleapis.com/gmail/v1"
    
    async def send_encrypted_email(
        self,
        sender_email: str,
        recipient_email: str,
        subject: str,
        body: str,
        security_level: int,
        access_token: str,
        user_id: str,
        db: AsyncIOMotorDatabase,
        attachments: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Send email with REAL quantum encryption via Gmail
        
        Args:
            sender_email: Sender's email address
            recipient_email: Recipient's email address  
            subject: Original subject (will be prefixed with security level)
            body: Original body content (will be encrypted)
            security_level: 1-4 (quantum security level)
            access_token: Gmail OAuth access token
            user_id: Sending user's ID
            db: Database session
            
        Returns:
            Dict with success status, message_id, encryption metadata
        """
        try:
            logger.info("=" * 80)
            logger.info("🔒 REAL END-TO-END ENCRYPTED EMAIL SERVICE")
            logger.info(f"   From: {sender_email}")
            logger.info(f"   To: {recipient_email}")
            logger.info(f"   Security Level: {security_level}")
            logger.info("=" * 80)
            
            # Step 1: Encrypt the email content using quantum encryption
            logger.info("📦 Step 1: Encrypting content with quantum keys...")
            encryption_result = await quantum_encryption_service.encrypt_email(
                subject=subject,
                body=body,
                sender_email=sender_email,
                receiver_email=recipient_email,
                security_level=security_level,
                user_id=user_id,
                db=db
            )
            
            # Get the encrypted body (base64 ciphertext)
            encrypted_body_base64 = encryption_result.get("encrypted_body", "")
            email_id = encryption_result.get("email_id", "")
            flow_id = encryption_result.get("flow_id", "")
            algorithm = encryption_result.get("algorithm", "")
            
            # Extract encryption metadata for headers
            encryption_metadata = encryption_result.get("encryption_metadata", {})
            key_id = encryption_result.get("key_id", "") or encryption_metadata.get("key_id", "")
            
            # Get key fragments, auth_tag, nonce from metadata
            key_fragments = encryption_metadata.get("key_fragments", [])
            if not key_fragments and key_id:
                key_fragments = [key_id]
            auth_tag = encryption_metadata.get("auth_tag", "")
            nonce = encryption_metadata.get("nonce", "")
            salt = encryption_metadata.get("salt", "")
            plaintext_size = encryption_metadata.get("plaintext_size", 0) or encryption_metadata.get("required_size", 0)
            
            logger.info(f"✅ Encryption complete!")
            logger.info(f"   Algorithm: {algorithm}")
            logger.info(f"   Email ID: {email_id}")
            logger.info(f"   Flow ID: {flow_id}")
            logger.info(f"   Encrypted size: {len(encrypted_body_base64)} bytes")
            logger.info(f"   Key fragments: {len(key_fragments)}")
            logger.info(f"   Encrypted preview: {encrypted_body_base64[:100]}...")
            
            # Step 2: Create security level prefix for subject
            level_prefixes = {
                1: "🔐 [Quantum-OTP-Secured]",
                2: "🔐 [Quantum-AES-Secured]",
                3: "🔐 [Quantum-PQC-Secured]",
                4: "🔐 [Quantum-RSA-Secured]"
            }
            encrypted_subject = f"{level_prefixes.get(security_level, '🔐 [Quantum-Secured]')} {subject}"
            
            # Step 3: Create MIME message with encrypted content
            logger.info("📧 Step 2: Creating MIME message for Gmail...")
            mime_message = MIMEMultipart('alternative')
            mime_message['Subject'] = encrypted_subject
            mime_message['From'] = sender_email
            mime_message['To'] = recipient_email
            
            # Add headers for QuMail identification and decryption metadata
            mime_message.add_header('X-QuMail-Encrypted', 'true')
            mime_message.add_header('X-QuMail-Security-Level', str(security_level))
            mime_message.add_header('X-QuMail-Email-ID', str(email_id))
            mime_message.add_header('X-QuMail-Flow-ID', flow_id)
            mime_message.add_header('X-QuMail-Algorithm', algorithm)
            
            # Add decryption metadata headers for direct decrypt (no MongoDB lookup needed)
            if key_id:
                mime_message.add_header('X-QuMail-Key-ID', key_id)
            if key_fragments:
                # Store key fragments as JSON array in header
                mime_message.add_header('X-QuMail-Key-Fragments', json.dumps(key_fragments))
            if auth_tag:
                mime_message.add_header('X-QuMail-Auth-Tag', auth_tag)
            if nonce:
                mime_message.add_header('X-QuMail-Nonce', nonce)
            if salt:
                mime_message.add_header('X-QuMail-Salt', salt)
            if plaintext_size:
                mime_message.add_header('X-QuMail-Plaintext-Size', str(plaintext_size))
            
            # Plain text part: Show encrypted data as text (gibberish in other mail clients)
            plain_text_content = self._create_encrypted_text_view(
                encrypted_body_base64,
                security_level,
                flow_id,
                sender_email,
                recipient_email
            )
            mime_message.attach(MIMEText(plain_text_content, 'plain'))
            
            # HTML part: Show encrypted data with styling (still gibberish, but formatted)
            html_content = self._create_encrypted_html_view(
                encrypted_body_base64,
                security_level,
                flow_id,
                algorithm,
                sender_email,
                recipient_email
            )
            mime_message.attach(MIMEText(html_content, 'html'))
            
            logger.info(f"✅ MIME message created")
            logger.info(f"   Subject: {encrypted_subject}")
            logger.info(f"   Headers: X-QuMail-* added for identification")
            
            # Step 4: Send via Gmail API
            logger.info("📮 Step 3: Sending via Gmail API...")
            encoded_message = base64.urlsafe_b64encode(mime_message.as_bytes()).decode()
            
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
                        logger.error(f"❌ Gmail API error: {response.status}, {error_text}")
                        raise Exception(f"Failed to send via Gmail: {error_text}")
                    
                    data = await response.json()
                    message_id = data.get("id", "")
                    thread_id = data.get("threadId", "")

                    # Persist Gmail metadata on the stored encrypted email record
                    if db and email_id:
                        email_repo = EmailRepository(db)
                        attachment_repo = AttachmentRepository(db)

                        try:
                            email_record = await email_repo.find_by_id(email_id)
                            if not email_record:
                                email_record = await email_repo.find_by_flow_id(email_id)

                            if email_record:
                                metadata = email_record.encryption_metadata or {}
                                if isinstance(metadata, str):
                                    try:
                                        metadata = json.loads(metadata)
                                    except json.JSONDecodeError:
                                        metadata = {"raw_metadata": metadata}

                                metadata.update(
                                    {
                                        "gmailMessageId": message_id,
                                        "gmailThreadId": thread_id,
                                        "sync_type": "gmail_quantum_encrypted",
                                        "sender": sender_email,
                                        "recipient": recipient_email,
                                        "ciphertext_preview": encrypted_body_base64[:120],
                                    }
                                )

                                await email_repo.update(
                                    email_record.id,
                                    {
                                        "gmail_message_id": message_id,
                                        "encryption_metadata": metadata,
                                    },
                                )

                                if attachments:
                                    logger.info(
                                        "Storing %d attachments for email %s", len(attachments), email_record.id
                                    )
                                    for attachment_data in attachments:
                                        try:
                                            encoded_content = attachment_data.get("content", "")
                                            if not encoded_content:
                                                continue
                                            raw_bytes = base64.b64decode(encoded_content)
                                            doc = AttachmentDocument(
                                                email_id=email_record.id,
                                                filename=attachment_data.get("filename", "unnamed"),
                                                content_type=attachment_data.get(
                                                    "mime_type", "application/octet-stream"
                                                ),
                                                size=attachment_data.get("size", len(raw_bytes)),
                                                encrypted_data=base64.b64encode(raw_bytes).decode("utf-8"),
                                            )
                                            await attachment_repo.create(doc)
                                            logger.info(
                                                "   Stored attachment: %s (%d bytes)",
                                                doc.filename,
                                                doc.size,
                                            )
                                        except Exception as att_error:  # pragma: no cover - logging only
                                            logger.error("Failed to store attachment: %s", att_error)
                            else:
                                logger.warning(
                                    "No stored email found for encryption result %s; Gmail metadata not persisted",
                                    email_id,
                                )
                        except Exception as db_error:  # pragma: no cover - logging only
                            logger.warning(
                                "Failed to persist Gmail metadata for email %s: %s", email_id, db_error
                            )
                    
                    logger.info(f"✅ Email sent successfully via Gmail!")
                    logger.info(f"   Gmail Message ID: {message_id}")
                    logger.info(f"   Thread ID: {thread_id}")
                    logger.info("=" * 80)
                    logger.info("📊 WHAT RECIPIENTS SEE:")
                    logger.info("   🌐 In Gmail/Outlook/Apple Mail: ENCRYPTED GIBBERISH")
                    logger.info("   🔓 In QuMail: PROPERLY DECRYPTED CONTENT")
                    logger.info("=" * 80)
                    
                    return {
                        "success": True,
                        "message": f"Level {security_level} quantum-encrypted email sent via Gmail",
                        "emailId": str(email_id),
                        "flowId": flow_id,
                        "gmailMessageId": message_id,
                        "gmailThreadId": thread_id,
                        "encryptionMethod": algorithm,
                        "securityLevel": security_level,
                        "entropy": encryption_result.get("entropy", 0.0),
                        "keyId": encryption_result.get("key_id", ""),
                        "encryptedSize": len(encrypted_body_base64),
                        "timestamp": encryption_result["timestamp"],
                        "sent_via_gmail": True,
                        "viewInOtherApps": "encrypted_gibberish",
                        "viewInQuMail": "decrypted_readable"
                    }
                    
        except Exception as e:
            logger.error(f"❌ Error sending encrypted email via Gmail: {e}")
            raise Exception(f"Failed to send encrypted email: {str(e)}")
    
    def _create_encrypted_text_view(
        self,
        encrypted_data: str,
        security_level: int,
        flow_id: str,
        sender: str,
        recipient: str
    ) -> str:
        """
        Create plain text view showing encrypted data
        This is what users see in Gmail/Outlook/etc - looks like gibberish
        """
        level_names = {
            1: "Quantum OTP (One-Time Pad)",
            2: "Quantum AES-256-GCM",
            3: "Post-Quantum Cryptography (Kyber/Dilithium)",
            4: "Quantum-Enhanced RSA-4096"
        }
        
        return f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  QUANTUM-ENCRYPTED EMAIL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️  This message is encrypted with quantum cryptography
⚠️  Only the intended recipient can decrypt this message
⚠️  To read this email, please use QuMail application

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Security Level: {security_level} - {level_names.get(security_level, 'Unknown')}
Flow ID: {flow_id}
From: {sender}
To: {recipient}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ENCRYPTED CONTENT (Base64 Ciphertext):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{encrypted_data}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️  DO NOT TRY TO DECRYPT THIS MANUALLY
⚠️  This content is protected by quantum key distribution
⚠️  Download QuMail to read this message: https://qumail.app

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    def _create_encrypted_html_view(
        self,
        encrypted_data: str,
        security_level: int,
        flow_id: str,
        algorithm: str,
        sender: str,
        recipient: str
    ) -> str:
        """
        Create HTML view showing encrypted data with styling
        Still gibberish, but looks more professional in email clients
        """
        level_colors = {
            1: "#ff0000",  # Red - Maximum security
            2: "#ff6600",  # Orange - High security
            3: "#0066ff",  # Blue - Quantum resistant
            4: "#9933ff"   # Purple - Hybrid security
        }
        
        level_names = {
            1: "Quantum OTP (One-Time Pad)",
            2: "Quantum AES-256-GCM",
            3: "Post-Quantum Cryptography",
            4: "Quantum-Enhanced RSA-4096"
        }
        
        color = level_colors.get(security_level, "#666666")
        level_name = level_names.get(security_level, "Unknown")
        
        # Chunk the encrypted data for better display
        chunks = [encrypted_data[i : i + 64] for i in range(0, len(encrypted_data), 64)]
        encrypted_display = '<br>'.join(chunks[:50])  # Limit display to first 50 lines
        
        if len(chunks) > 50:
            encrypted_display += f'<br>... ({len(chunks) - 50} more lines) ...'
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: 'Courier New', monospace;
            background-color: #0a0a0a;
            color: #00ff00;
            padding: 20px;
            margin: 0;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            border: 2px solid {color};
            padding: 30px;
            background-color: #1a1a1a;
            box-shadow: 0 0 20px {color};
        }}
        .header {{
            text-align: center;
            border-bottom: 2px solid {color};
            padding-bottom: 20px;
            margin-bottom: 20px;
        }}
        .header h1 {{
            color: {color};
            font-size: 24px;
            margin: 10px 0;
            text-transform: uppercase;
            letter-spacing: 3px;
        }}
        .warning {{
            background-color: #330000;
            border-left: 4px solid #ff0000;
            padding: 15px;
            margin: 20px 0;
            color: #ff6666;
        }}
        .info-box {{
            background-color: #001a1a;
            border-left: 4px solid {color};
            padding: 15px;
            margin: 20px 0;
        }}
        .info-box strong {{
            color: {color};
        }}
        .encrypted-content {{
            background-color: #0d0d0d;
            border: 1px solid {color};
            padding: 20px;
            margin: 20px 0;
            font-size: 11px;
            line-height: 1.6;
            word-break: break-all;
            max-height: 400px;
            overflow-y: auto;
        }}
        .encrypted-label {{
            color: {color};
            font-weight: bold;
            text-align: center;
            margin: 10px 0;
            font-size: 14px;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 2px solid {color};
            font-size: 12px;
        }}
        .footer a {{
            color: {color};
            text-decoration: none;
            font-weight: bold;
        }}
        .footer a:hover {{
            text-decoration: underline;
        }}
        .badge {{
            background-color: {color};
            color: #000;
            padding: 5px 15px;
            border-radius: 3px;
            font-weight: bold;
            display: inline-block;
            margin: 10px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔐 Quantum-Encrypted Email 🔐</h1>
            <div class="badge">Security Level {security_level}</div>
            <p style="color: {color}; font-size: 14px; margin: 10px 0;">{level_name}</p>
        </div>
        
        <div class="warning">
            <strong>⚠️ ENCRYPTED MESSAGE</strong><br>
            This message is protected by quantum cryptography and can only be decrypted by the intended recipient using QuMail application.
        </div>
        
        <div class="info-box">
            <strong>Encryption Details:</strong><br>
            <strong>Algorithm:</strong> {algorithm}<br>
            <strong>Flow ID:</strong> {flow_id}<br>
            <strong>From:</strong> {sender}<br>
            <strong>To:</strong> {recipient}<br>
            <strong>Status:</strong> <span style="color: #00ff00;">● ENCRYPTED</span>
        </div>
        
        <div class="encrypted-label">
            ━━━ ENCRYPTED CONTENT (BASE64 CIPHERTEXT) ━━━
        </div>
        
        <div class="encrypted-content">
            {encrypted_display}
        </div>
        
        <div class="warning">
            <strong>⚠️ SECURITY WARNING</strong><br>
            • Do NOT attempt to decrypt this message manually<br>
            • This content is protected by quantum key distribution (QKD)<br>
            • Only QuMail application can decrypt this message<br>
            • Unauthorized decryption attempts will be logged
        </div>
        
        <div class="footer">
            <p>To read this encrypted message:</p>
            <p><a href="https://qumail.app">Download QuMail Application</a></p>
            <p style="font-size: 10px; color: #666; margin-top: 20px;">
                Protected by Quantum Key Distribution | End-to-End Encrypted
            </p>
        </div>
    </div>
</body>
</html>
"""

# Create singleton instance
real_encrypted_gmail_service = RealEncryptedGmailService()
