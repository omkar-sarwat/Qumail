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
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Set

from email.utils import parseaddr

from ..mongo_models import (
    EmailDocument, EmailDirection, KeyUsageDocument,
    QKDKeyDocument, QKDKeyState, QKDSessionDocument, QKDAuditLogDocument
)
from ..mongo_repositories import (
    EmailRepository, KeyUsageRepository, UserRepository,
    QKDKeyRepository, QKDSessionRepository, QKDAuditLogRepository
)
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
        db: Any = None,
        gmail_credentials: Dict = None
    ) -> Dict[str, Any]:
        """
        Send email with specified security level encryption
        
        Flow:
        1. Verify recipient is a registered QuMail user
        2. Encrypt subject and body with chosen security level
        3. Store encryption metadata in local database
        4. Send encrypted content to Gmail
        5. Gmail stores only encrypted data
        """
        try:
            logger.info(f"Sending encrypted email with security level {security_level}")
            
            # ========== QUMAIL USER VERIFICATION ==========
            # Only allow sending encrypted emails to registered QuMail users
            # Non-QuMail users cannot decrypt quantum-encrypted emails
            if db is not None:
                user_repo = UserRepository(db)
                
                # Check if recipient is a registered QuMail user
                recipient_user = await user_repo.find_by_email(recipient_email)
                
                if not recipient_user:
                    logger.warning(f"Recipient {recipient_email} is NOT a registered QuMail user - blocking encrypted email")
                    return {
                        'success': False,
                        'error': 'recipient_not_qumail_user',
                        'message': f"Cannot send encrypted email to {recipient_email}. Recipient is not a registered QuMail user and cannot decrypt quantum-encrypted emails. Please ask them to register at QuMail first.",
                        'recipient_email': recipient_email
                    }
                
                # UserDocument stores Mongo `_id` as `id`, so use that instead of a non-existent `user_id` attribute
                logger.info(f"✓ Recipient {recipient_email} verified as QuMail user (ID: {recipient_user.id})")
            else:
                logger.warning("No database connection - skipping QuMail user verification")
            # ================================================
            
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
            
            # Encrypt based on security level (pass both sender and receiver for KME key association)
            encryption_result = await self._encrypt_by_level(
                security_level, message_json, sender_email, recipient_email
            )
            
            # Generate unique flow ID
            flow_id = encryption_result['metadata'].get('flow_id', str(uuid.uuid4()))
            
            # Extract metadata for storage (tested functions use nested metadata)
            metadata = self._normalize_metadata(encryption_result.get('metadata'))

            encrypted_data = encryption_result.get('encrypted_content', encryption_result.get('encrypted_data'))
            
            allowed_email_set = self._collect_allowed_email_set(
                sender_email,
                recipient_email,
                cc,
                bcc
            )
            allowed_email_list = sorted(allowed_email_set) if allowed_email_set else None

            # ========== STORE QKD DATA IN MONGODB ==========
            # Store quantum key information in MongoDB for full lifecycle tracking
            if db is not None and (metadata.get('key_id') or metadata.get('key_fragments')):
                try:
                    qkd_key_repo = QKDKeyRepository(db)
                    qkd_audit_repo = QKDAuditLogRepository(db)
                    qkd_session_repo = QKDSessionRepository(db)
                    
                    # Create QKD Session for this email
                    qkd_session = QKDSessionDocument(
                        flow_id=flow_id,
                        sender_email=sender_email,
                        sender_sae_id="25840139-0dd4-49ae-ba1e-b86731601803",  # KME1 SAE ID
                        receiver_email=recipient_email,
                        receiver_sae_id="c565d5aa-8670-4446-8471-b0e53e315d2a",  # KME2 SAE ID
                        security_level=security_level,
                        encryption_algorithm=encryption_result.get('algorithm'),
                        is_active=False,  # Session completes immediately for email
                        is_successful=True,
                        completed_at=datetime.utcnow(),
                        expires_at=datetime.utcnow() + timedelta(hours=24)
                    )
                    await qkd_session_repo.create(qkd_session)
                    
                    # Store individual QKD keys
                    key_fragments = metadata.get('key_fragments', [])
                    if not key_fragments and metadata.get('key_id'):
                        key_fragments = [metadata.get('key_id')]
                    
                    for idx, key_id in enumerate(key_fragments):
                        qkd_key = QKDKeyDocument(
                            key_id=key_id,
                            kme1_key_id=key_id,
                            source_kme="KME1",
                            sae1_id="25840139-0dd4-49ae-ba1e-b86731601803",
                            sae2_id="c565d5aa-8670-4446-8471-b0e53e315d2a",
                            sender_email=sender_email,
                            receiver_email=recipient_email,
                            flow_id=flow_id,
                            security_level=security_level,
                            algorithm=encryption_result.get('algorithm'),
                            state=QKDKeyState.CONSUMED,  # Key is consumed immediately for email
                            is_consumed=True,
                            consumed_by=sender_user_id,
                            consumed_at=datetime.utcnow(),
                            key_size_bits=metadata.get('key_size', 256) * 8 if metadata.get('key_size') else 256,
                            expires_at=datetime.utcnow() + timedelta(hours=24),
                            quantum_grade=True,
                            entropy_score=metadata.get('entropy', 1.0),
                            operation_history=[{
                                "operation": "USED_FOR_EMAIL_ENCRYPTION",
                                "timestamp": datetime.utcnow().isoformat(),
                                "flow_id": flow_id,
                                "security_level": security_level
                            }]
                        )
                        await qkd_key_repo.create(qkd_key)
                        
                        # Add key to session
                        await qkd_session_repo.add_key_to_session(
                            qkd_session.session_id, 
                            key_id,
                            key_size_bits=qkd_key.key_size_bits
                        )
                    
                    # Log the QKD operation
                    await qkd_audit_repo.log_operation(
                        operation="EMAIL_ENCRYPTED",
                        key_id=metadata.get('key_id'),
                        session_id=qkd_session.session_id,
                        flow_id=flow_id,
                        user_email=sender_email,
                        user_id=sender_user_id,
                        success=True,
                        details={
                            "security_level": security_level,
                            "algorithm": encryption_result.get('algorithm'),
                            "receiver_email": recipient_email,
                            "key_count": len(key_fragments),
                            "encrypted_size": len(encrypted_data) if encrypted_data else 0
                        }
                    )
                    
                    logger.info(f"[QKD MongoDB] Stored {len(key_fragments)} key(s) and session for flow {flow_id}")
                    
                except Exception as qkd_err:
                    logger.warning(f"[QKD MongoDB] Failed to store QKD data: {qkd_err}")
                    # Don't fail the email send if QKD storage fails
            # ================================================

            # Create email record in database with encryption metadata
            # Store auth_tag in metadata so it's available during decryption
            if encryption_result.get('auth_tag'):
                metadata['auth_tag'] = encryption_result['auth_tag']
            elif encryption_result.get('signature'):
                # Fallback for legacy/RSA
                metadata['signature'] = encryption_result['signature']
            
            # Extract public keys for explicit MongoDB storage (Level 3 and 4)
            rsa_public_key = metadata.get('public_key')  # Level 4
            kem_public_key = metadata.get('kem_public_key') or metadata.get('kyber_public_key')  # Level 3
            dsa_public_key = metadata.get('dsa_public_key') or metadata.get('dilithium_public_key')  # Level 3
            private_key_ref = metadata.get('private_key_ref')  # Reference to local private key
            
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
                allowed_emails=allowed_email_list,
                # Store encryption metadata
                encryption_key_id=metadata.get('key_id', metadata.get('key_ids', {}).get('km1', '')),
                encryption_algorithm=encryption_result.get('algorithm'),
                encryption_iv=metadata.get('nonce'),  # 'nonce' in tested functions
                encryption_auth_tag=encryption_result.get('auth_tag') or encryption_result.get('signature'),  # Prefer auth_tag
                encryption_metadata=metadata,  # Stored as structured metadata for quick access
                # Explicit public key fields for Level 3 and 4 (stored in MongoDB)
                rsa_public_key=rsa_public_key,
                kem_public_key=kem_public_key,
                dsa_public_key=dsa_public_key,
                private_key_ref=private_key_ref,
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
                    att_content = att_data.get('content', '')
                    if att_content:
                        try:
                            attachment_level = self._resolve_attachment_level(security_level)
                            logger.info(
                                "Encrypting attachment %d/%d (%s) with security level %d",
                                idx + 1,
                                len(attachments),
                                att_data.get('filename', 'unknown'),
                                attachment_level
                            )
                            att_encrypted = await self._encrypt_by_level(attachment_level, att_content, sender_email)

                            encrypted_att_content = att_encrypted.get('encrypted_content', att_encrypted.get('encrypted_data'))
                            att_metadata = self._normalize_metadata(att_encrypted.get('metadata'))

                            if att_encrypted.get('auth_tag'):
                                att_metadata.setdefault('auth_tag', att_encrypted['auth_tag'])
                            if att_encrypted.get('signature'):
                                att_metadata.setdefault('signature', att_encrypted['signature'])

                            attachment_flow_id = att_metadata.get('flow_id') or f"{flow_id}-att-{idx+1}"
                            att_metadata['flow_id'] = attachment_flow_id
                            attachment_key_id = att_metadata.get('key_id', att_metadata.get('key_ids', {}).get('km1', ''))

                            # Store encrypted attachment
                            from ..mongo_models import AttachmentDocument
                            att_doc = AttachmentDocument(
                                email_id=email.id,
                                filename=att_data.get('filename', 'attachment'),
                                content_type=att_data.get('mimeType', 'application/octet-stream'),
                                size=len(att_content),
                                encrypted_data=encrypted_att_content if isinstance(encrypted_att_content, str) else base64.b64encode(encrypted_att_content).decode('utf-8'),
                                security_level=attachment_level,
                                flow_id=attachment_flow_id,
                                encryption_algorithm=att_encrypted.get('algorithm'),
                                encryption_metadata=att_metadata,
                                encryption_key_id=attachment_key_id,
                                encryption_auth_tag=att_encrypted.get('auth_tag') or att_encrypted.get('signature')
                            )
                            
                            saved_att = await attachment_repo.create(att_doc)
                            attachment_ids.append(saved_att.id)
                            logger.info(f"✓ Attachment encrypted and stored: {att_doc.filename} ({att_doc.size} bytes) [L{attachment_level}]")
                        except Exception as att_error:
                            logger.error(f"Failed to encrypt attachment {att_data.get('filename', 'unknown')}: {att_error}")
                            # Continue with other attachments even if one fails
            
            # Send encrypted email via Gmail
            if gmail_credentials:
                try:
                    from .gmail_service import gmail_service
                    
                    # Prepare encrypted email for Gmail
                    encrypted_subject = f"🔐 QuMail Encrypted L{security_level}"
                    
                    # Extract key_id from multiple possible sources
                    key_id = (
                        metadata.get('key_id') or 
                        metadata.get('key_ids', {}).get('km1') or 
                        encryption_result.get('key_id') or
                        encryption_result.get('metadata', {}).get('quantum_enhancement', {}).get('key_ids', {}).get('km1') or
                        flow_id  # Fallback to flow_id as identifier
                    )
                    
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
                    headers = {
                        'X-QuMail-Flow-ID': flow_id,
                        'X-QuMail-Key-ID': key_id,
                        'X-QuMail-Algorithm': encryption_result.get('algorithm', 'unknown'),
                        'X-QuMail-Security-Level': str(security_level),
                        'X-QuMail-Auth-Tag': metadata.get('auth_tag', ''),
                        'X-QuMail-Nonce': metadata.get('nonce', '')
                    }

                    if metadata.get('salt'):
                        headers['X-QuMail-Salt'] = metadata['salt']

                    if metadata.get('required_size') is not None:
                        headers['X-QuMail-Plaintext-Size'] = str(metadata['required_size'])
                    if metadata.get('key_size') is not None:
                        headers['X-QuMail-Total-Key-Bytes'] = str(metadata['key_size'])

                    key_fragments_header = metadata.get('key_fragments')
                    if key_fragments_header:
                        try:
                            headers['X-QuMail-Key-Fragments'] = json.dumps(key_fragments_header)
                        except (TypeError, ValueError):
                            headers['X-QuMail-Key-Fragments'] = ','.join(map(str, key_fragments_header))

                    key_ids = metadata.get('key_ids') or {}
                    if key_ids:
                        try:
                            headers['X-QuMail-Key-IDs'] = json.dumps(key_ids)
                        except (TypeError, ValueError):
                            logger.warning("Failed to serialize key_ids for Gmail headers", exc_info=True)

                    # Add Level 3 PQC-specific headers
                    if security_level == 3:
                        if metadata.get('kem_ciphertext'):
                            headers['X-QuMail-KEM-Ciphertext'] = metadata['kem_ciphertext']
                        if metadata.get('kem_secret_key'):
                            headers['X-QuMail-KEM-Secret-Key'] = metadata['kem_secret_key']
                        if metadata.get('kem_public_key'):
                            headers['X-QuMail-KEM-Public-Key'] = metadata['kem_public_key']
                        if metadata.get('dsa_public_key'):
                            headers['X-QuMail-DSA-Public-Key'] = metadata['dsa_public_key']
                        if metadata.get('signature'):
                            headers['X-QuMail-Signature'] = metadata['signature']
                        quantum_enhancement = metadata.get('quantum_enhancement', {})
                        if quantum_enhancement:
                            try:
                                headers['X-QuMail-Quantum-Enhancement'] = json.dumps(quantum_enhancement)
                            except (TypeError, ValueError):
                                logger.warning("Failed to serialize quantum_enhancement for Gmail headers")

                    # Add Level 4 RSA-specific headers
                    if security_level == 4:
                        if metadata.get('encrypted_session_key'):
                            headers['X-QuMail-Encrypted-Session-Key'] = metadata['encrypted_session_key']
                        if metadata.get('iv'):
                            headers['X-QuMail-IV'] = metadata['iv']
                        if metadata.get('aad'):
                            headers['X-QuMail-AAD'] = metadata['aad']
                        if metadata.get('public_key'):
                            headers['X-QuMail-Public-Key'] = metadata['public_key']
                        if metadata.get('private_key_ref'):
                            headers['X-QuMail-Private-Key-Ref'] = metadata['private_key_ref']
                        if metadata.get('signature'):
                            headers['X-QuMail-Signature'] = metadata['signature']

                    message = {
                        'from': sender_email,
                        'to': recipient_email,
                        'subject': encrypted_subject,
                        'bodyText': encrypted_body_text,
                        'bodyHtml': encrypted_body_html,
                        'cc': cc,
                        'bcc': bcc,
                        'headers': headers
                    }
                    
                    # Send via Gmail
                    result = await gmail_service.send_email(access_token, message)
                    gmail_message_id = result.get('messageId')
                    
                    # Store Gmail message ID for sender's record
                    await email_repo.update(email.id, {"gmail_message_id": gmail_message_id})
                    email.gmail_message_id = gmail_message_id
                    
                    # Also create a receiver-side email document so the recipient can decrypt
                    # This is crucial for the receiver to have the encryption metadata
                    try:
                        # Find the recipient's user record (if they exist in our system)
                        user_repo = UserRepository(db)
                        recipient_user = await user_repo.find_by_email(recipient_email)
                        
                        if recipient_user:
                            # Create email document for the recipient
                            receiver_email_doc = EmailDocument(
                                flow_id=flow_id,  # Same flow_id for linking
                                user_id=str(recipient_user.id),
                                sender_email=sender_email,
                                receiver_email=recipient_email,
                                subject=f"[ENCRYPTED-L{security_level}] {subject[:50]}...",
                                body_encrypted=encrypted_data,
                                security_level=security_level,
                                direction=EmailDirection.RECEIVED,
                                timestamp=datetime.utcnow(),
                                is_read=False,
                                is_starred=False,
                                is_suspicious=False,
                                allowed_emails=allowed_email_list,
                                gmail_message_id=gmail_message_id,
                                # Copy all encryption metadata
                                encryption_key_id=metadata.get('key_id', metadata.get('key_ids', {}).get('km1', '')),
                                encryption_algorithm=encryption_result.get('algorithm'),
                                encryption_iv=metadata.get('nonce'),
                                encryption_auth_tag=encryption_result.get('auth_tag') or encryption_result.get('signature'),
                                encryption_metadata=metadata
                            )
                            await email_repo.create(receiver_email_doc)
                            logger.info(f"Created receiver-side email document for {recipient_email} with flow_id {flow_id}")
                        else:
                            logger.info(f"Recipient {recipient_email} not registered in QuMail - they can still decrypt via Gmail headers")
                    except Exception as receiver_doc_error:
                        logger.warning(f"Failed to create receiver email document: {receiver_doc_error}")
                        # Non-fatal, continue
                    
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

    @staticmethod
    def _normalize_email_address(value: Optional[Any]) -> Optional[str]:
        """Return a consistently lowercased email string if present."""
        if not value:
            return None
        if isinstance(value, bytes):
            value = value.decode('utf-8', errors='ignore')
        name, email_addr = parseaddr(str(value))
        candidate = email_addr or str(value)
        candidate = candidate.strip().lower()
        return candidate or None

    @classmethod
    def _expand_address_field(cls, field: Optional[Any]) -> Set[str]:
        """Expand list/dict/string representations into a normalized email set."""
        emails: Set[str] = set()
        if not field:
            return emails
        if isinstance(field, (list, tuple, set)):
            items = field
        else:
            items = [field]
        for item in items:
            candidate: Optional[Any] = None
            if isinstance(item, dict):
                candidate = (
                    item.get('email')
                    or item.get('value')
                    or item.get('address')
                    or item.get('to')
                )
            else:
                candidate = item
            if not candidate:
                continue
            for segment in str(candidate).split(','):
                normalized = cls._normalize_email_address(segment)
                if normalized:
                    emails.add(normalized)
        return emails

    @classmethod
    def _collect_allowed_email_set(
        cls,
        sender_email: Optional[str],
        primary_recipient: Optional[str],
        cc: Optional[Any] = None,
        bcc: Optional[Any] = None,
        extra_addresses: Optional[List[str]] = None
    ) -> Set[str]:
        """Build the normalized set of participants allowed to decrypt."""
        allowed: Set[str] = set()
        for entry in (sender_email, primary_recipient):
            normalized = cls._normalize_email_address(entry)
            if normalized:
                allowed.add(normalized)
        allowed.update(cls._expand_address_field(cc))
        allowed.update(cls._expand_address_field(bcc))
        if extra_addresses:
            allowed.update(cls._expand_address_field(extra_addresses))
        return allowed

    async def _encrypt_by_level(self, security_level: int, content: str, 
                                 sender_email: str, receiver_email: str = '') -> Dict[str, Any]:
        """Route encryption requests to the correct level while validating input.
        
        Args:
            security_level: Encryption level (1-4)
            content: Content to encrypt
            sender_email: Sender's email for key association
            receiver_email: Receiver's email for key association
        """
        if security_level == 1:
            return await self.encryption_service.encrypt_level_1_otp(content, sender_email, receiver_email)
        if security_level == 2:
            return await self.encryption_service.encrypt_level_2_aes(content, sender_email, receiver_email)
        if security_level == 3:
            return await self.encryption_service.encrypt_level_3_pqc(content, sender_email, receiver_email)
        if security_level == 4:
            return await self.encryption_service.encrypt_level_4_standard(content, sender_email, receiver_email)
        raise ValueError(f"Invalid security level: {security_level}")

    async def _decrypt_by_level(
        self,
        security_level: int,
        encrypted_data: str,
        metadata: Dict[str, Any],
        user_email: str
    ) -> bytes:
        """Route decryption requests to the appropriate level."""
        if security_level == 1:
            return await self.encryption_service.decrypt_level_1_otp(encrypted_data, metadata, user_email)
        if security_level == 2:
            return await self.encryption_service.decrypt_level_2_aes(encrypted_data, metadata, user_email)
        if security_level == 3:
            return await self.encryption_service.decrypt_level_3_pqc(encrypted_data, metadata, user_email)
        if security_level == 4:
            return await self.encryption_service.decrypt_level_4_standard(encrypted_data, metadata, user_email)
        raise ValueError(f"Invalid security level: {security_level}")

    @staticmethod
    def _normalize_metadata(raw_metadata: Optional[Any]) -> Dict[str, Any]:
        """Ensure encryption metadata is always a mutable dictionary."""
        if not raw_metadata:
            return {}
        if isinstance(raw_metadata, dict):
            return dict(raw_metadata)
        if isinstance(raw_metadata, str):
            try:
                parsed = json.loads(raw_metadata)
                return parsed if isinstance(parsed, dict) else {'raw_metadata': parsed}
            except json.JSONDecodeError:
                return {'raw_metadata': raw_metadata}
        return dict(raw_metadata)

    def _resolve_attachment_level(self, requested_level: Optional[int]) -> int:
        """Attachments support security levels 2-4; fallback to Level 4 otherwise."""
        if requested_level in (2, 3, 4):
            return requested_level
        if requested_level and requested_level != 4:
            logger.info(
                "Attachment security level %s unsupported; defaulting to Level 4",
                requested_level
            )
        return 4
    
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
        db: Any
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
                                attachment_level = self._resolve_attachment_level(att.security_level or email.security_level)
                                att_metadata = self._normalize_metadata(att.encryption_metadata)
                                att_metadata.setdefault('flow_id', att.flow_id or email.flow_id)
                                logger.info(
                                    "Decrypting attachment for cached email: %s using level %d",
                                    att.filename,
                                    attachment_level
                                )
                                decrypted_att = await self._decrypt_by_level(
                                    attachment_level,
                                    att.encrypted_data,
                                    att_metadata,
                                    email.receiver_email
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
                            'mime_type': att.content_type,
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
            
            # Handle non-encrypted emails (security level 0)
            if email.security_level == 0 or email.security_level is None:
                logger.info(f"Email {email_id} is not quantum-encrypted (level 0), returning plain content")
                # For non-encrypted emails, just return the body as-is
                plain_body = email.body_encrypted or email.decrypted_body or ""
                
                # Try to parse as JSON message data, or create simple message
                try:
                    message_data = json.loads(plain_body)
                except (json.JSONDecodeError, TypeError):
                    message_data = {
                        'subject': email.subject,
                        'body': plain_body,
                        'from': email.sender_email,
                        'to': email.receiver_email
                    }
                
                # Mark as read
                await email_repo.mark_as_read(email.id)
                
                return {
                    'success': True,
                    'email_id': email.id,
                    'flow_id': email.flow_id,
                    'subject': message_data.get('subject', email.subject),
                    'body': message_data.get('body', plain_body),
                    'from': message_data.get('from', email.sender_email),
                    'to': message_data.get('to', email.receiver_email),
                    'timestamp': email.timestamp.isoformat() if email.timestamp else None,
                    'security_level': 0,
                    'algorithm': 'None',
                    'decrypted_at': datetime.utcnow().isoformat(),
                    'attachments': [],
                    'from_cache': False,
                    'is_plain_email': True
                }
            
            # Build metadata dict from stored fields
            metadata = {
                'flow_id': email.flow_id,
                'key_id': email.encryption_key_id,
                'algorithm': email.encryption_algorithm,
                'nonce': email.encryption_iv,
                'auth_tag': email.encryption_auth_tag
            }
            
            # Add any extra metadata from JSON field (handle legacy JSON strings)
            extra_metadata = self._normalize_metadata(email.encryption_metadata)
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
                        attachment_level = self._resolve_attachment_level(att.security_level or email.security_level)
                        att_metadata = self._normalize_metadata(att.encryption_metadata)
                        att_metadata.setdefault('flow_id', att.flow_id or email.flow_id)
                        
                        logger.info(
                            "Decrypting attachment: %s with level %d",
                            att.filename,
                            attachment_level
                        )
                        decrypted_att = await self._decrypt_by_level(
                            attachment_level,
                            att.encrypted_data,
                            att_metadata,
                            email.receiver_email
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
                        'mime_type': att.content_type,
                        'size': att.size
                    })
                    logger.info(f"✓ Decrypted attachment: {att.filename}")
                except Exception as att_error:
                    logger.error(f"Failed to decrypt attachment {att.filename}: {att_error}")
            
            # Cache the decrypted content for future use (no need to call KME again)
            email.decrypted_body = decrypted_json
            await email_repo.update(email.id, {"decrypted_body": decrypted_json})
            logger.info(f"✓ Cached decrypted content for email {email_id} - future views will be instant")
            
            # ========== LOG QKD DECRYPTION IN MONGODB ==========
            try:
                qkd_audit_repo = QKDAuditLogRepository(db)
                await qkd_audit_repo.log_operation(
                    operation="EMAIL_DECRYPTED",
                    key_id=email.encryption_key_id,
                    flow_id=email.flow_id,
                    user_email=email.receiver_email,
                    success=True,
                    details={
                        "security_level": email.security_level,
                        "algorithm": email.encryption_algorithm,
                        "sender_email": email.sender_email,
                        "attachment_count": len(decrypted_attachments)
                    }
                )
                logger.info(f"[QKD MongoDB] Logged decryption for flow {email.flow_id}")
            except Exception as qkd_err:
                logger.warning(f"[QKD MongoDB] Failed to log decryption: {qkd_err}")
            # ====================================================
            
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
        db: Any
    ) -> list:
        """
        Get list of encrypted emails (metadata only, no decryption)
        """
        try:
            # Determine direction based on folder
            if folder == 'sent':
                direction = EmailDirection.SENT
            else:  # inbox
                direction = EmailDirection.RECEIVED
            
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

    async def store_gmail_message_locally(
        self,
        gmail_msg: Dict[str, Any],
        user_email: str,
        user_id: str,
        db: Any
    ) -> Optional[EmailDocument]:
        """Persist a Gmail message (plain or encrypted) into the local store if missing."""
        try:
            if not gmail_msg:
                return None

            gmail_message_id = gmail_msg.get('id') or gmail_msg.get('gmailMessageId') or ""
            if not gmail_message_id:
                return None
            gmail_message_id = gmail_message_id.replace("gmail_", "", 1)

            email_repo = EmailRepository(db)
            existing_email = await email_repo.find_by_gmail_id(gmail_message_id)
            if existing_email:
                return existing_email

            subject = gmail_msg.get('subject') or '(No subject)'
            body_html = gmail_msg.get('bodyHtml')
            body_text = gmail_msg.get('bodyText') or gmail_msg.get('snippet') or ''
            if not body_text and body_html:
                body_text = re.sub('<[^<]+?>', '', body_html)

            sender_display = (
                gmail_msg.get('sender')
                or gmail_msg.get('from')
                or gmail_msg.get('from_email')
                or ''
            )
            recipient_display = gmail_msg.get('recipient') or user_email
            cc_value = gmail_msg.get('cc')
            bcc_value = gmail_msg.get('bcc')
            reply_to_value = gmail_msg.get('replyTo')
            sender_name, sender_email = parseaddr(sender_display)
            receiver_name, receiver_email = parseaddr(recipient_display)
            if not sender_email:
                sender_email = sender_display or user_email
            if not receiver_email:
                receiver_email = recipient_display or user_email

            allowed_email_set = self._collect_allowed_email_set(
                sender_email,
                receiver_email,
                cc=cc_value,
                bcc=bcc_value,
                extra_addresses=[reply_to_value, sender_display, recipient_display]
            )
            allowed_email_list = sorted(allowed_email_set) if allowed_email_set else None

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
                'gmailMessageId': gmail_message_id,
                'senderDisplay': sender_display,
                'receiverDisplay': recipient_display,
                'toHeader': recipient_display,
                'fromHeader': sender_display,
                'cc': cc_value,
                'bcc': bcc_value,
                'replyTo': reply_to_value
            }

            custom_headers = gmail_msg.get('customHeaders', {}) or {}
            is_qumail_encrypted = 'qumail encrypted' in subject.lower()
            security_level = 0
            encryption_algorithm = None
            encryption_key_id = None
            flow_id = None
            header_salt = None
            header_key_ids: Dict[str, str] = {}
            header_key_fragments: List[str] = []
            plaintext_size_header: Optional[int] = None
            total_key_bytes_header: Optional[int] = None

            if 'x-qumail-security-level' in custom_headers:
                try:
                    security_level = int(custom_headers['x-qumail-security-level'])
                    is_qumail_encrypted = True
                except ValueError:
                    security_level = 1

            if 'x-qumail-algorithm' in custom_headers:
                encryption_algorithm = custom_headers['x-qumail-algorithm']

            if 'x-qumail-key-id' in custom_headers:
                encryption_key_id = custom_headers['x-qumail-key-id']

            if 'x-qumail-flow-id' in custom_headers:
                flow_id = custom_headers['x-qumail-flow-id']

            if 'x-qumail-salt' in custom_headers:
                header_salt = custom_headers['x-qumail-salt']

            if 'x-qumail-key-ids' in custom_headers:
                raw_key_ids = custom_headers['x-qumail-key-ids']
                parsed_key_ids: Dict[str, str] = {}
                try:
                    parsed = json.loads(raw_key_ids)
                    if isinstance(parsed, dict):
                        parsed_key_ids = {str(k): str(v) for k, v in parsed.items() if v}
                except (json.JSONDecodeError, TypeError):
                    for segment in raw_key_ids.split(','):
                        if ':' in segment:
                            k, v = segment.split(':', 1)
                            parsed_key_ids[k.strip()] = v.strip()
                if parsed_key_ids:
                    header_key_ids = parsed_key_ids
                    if not encryption_key_id:
                        encryption_key_id = header_key_ids.get('km1') or next(iter(header_key_ids.values()), None)

            if 'x-qumail-key-fragments' in custom_headers:
                raw_fragments = custom_headers['x-qumail-key-fragments']
                parsed_fragments: List[str] = []
                try:
                    decoded = json.loads(raw_fragments)
                    if isinstance(decoded, list):
                        parsed_fragments = [str(item) for item in decoded if item]
                except (json.JSONDecodeError, TypeError):
                    parsed_fragments = [seg.strip() for seg in raw_fragments.split(',') if seg.strip()]
                if parsed_fragments:
                    header_key_fragments = parsed_fragments

            for header_name in ('x-qumail-plaintext-size', 'x-qumail-required-size'):
                if header_name in custom_headers and plaintext_size_header is None:
                    try:
                        plaintext_size_header = int(custom_headers[header_name])
                    except (ValueError, TypeError):
                        plaintext_size_header = None

            if 'x-qumail-total-key-bytes' in custom_headers:
                try:
                    total_key_bytes_header = int(custom_headers['x-qumail-total-key-bytes'])
                except (ValueError, TypeError):
                    total_key_bytes_header = None

            if is_qumail_encrypted:
                if not encryption_algorithm:
                    algorithm_match = re.search(r'Algorithm:\s*(.+)', body_text)
                    if algorithm_match:
                        encryption_algorithm = algorithm_match.group(1).strip()

                if not encryption_key_id:
                    key_match = re.search(r'Key ID:\s*(.+)', body_text)
                    if key_match:
                        encryption_key_id = key_match.group(1).strip()

                if not flow_id:
                    flow_match = re.search(r'Flow ID:\s*(.+)', body_text)
                    if flow_match:
                        flow_id = flow_match.group(1).strip()

            # Subject fallback for legacy formats (e.g., L2, etc.)
            if not security_level and is_qumail_encrypted:
                level_match = re.search(r'L(\d)', subject)
                if level_match:
                    security_level = int(level_match.group(1))
                else:
                    security_level = 1

            if not flow_id:
                flow_id = f"gmail:{gmail_message_id}"

            if 'x-qumail-auth-tag' in custom_headers:
                metadata['auth_tag'] = custom_headers['x-qumail-auth-tag']
            if 'x-qumail-nonce' in custom_headers:
                metadata['nonce'] = custom_headers['x-qumail-nonce']
            if header_salt:
                metadata['salt'] = header_salt
            if header_key_ids:
                metadata['key_ids'] = header_key_ids
            if header_key_fragments:
                metadata['key_fragments'] = header_key_fragments
            if plaintext_size_header is not None:
                metadata['required_size'] = plaintext_size_header
            if total_key_bytes_header is not None:
                metadata['key_size'] = total_key_bytes_header

            # Extract Level 3 PQC-specific headers
            if 'x-qumail-kem-ciphertext' in custom_headers:
                metadata['kem_ciphertext'] = custom_headers['x-qumail-kem-ciphertext']
                metadata['kyber_ciphertext'] = custom_headers['x-qumail-kem-ciphertext']  # Legacy alias
            if 'x-qumail-kem-secret-key' in custom_headers:
                metadata['kem_secret_key'] = custom_headers['x-qumail-kem-secret-key']
                metadata['kyber_private_key'] = custom_headers['x-qumail-kem-secret-key']  # Legacy alias
            if 'x-qumail-kem-public-key' in custom_headers:
                metadata['kem_public_key'] = custom_headers['x-qumail-kem-public-key']
                metadata['kyber_public_key'] = custom_headers['x-qumail-kem-public-key']  # Legacy alias
            if 'x-qumail-dsa-public-key' in custom_headers:
                metadata['dsa_public_key'] = custom_headers['x-qumail-dsa-public-key']
                metadata['dilithium_public_key'] = custom_headers['x-qumail-dsa-public-key']  # Legacy alias
            if 'x-qumail-signature' in custom_headers:
                metadata['signature'] = custom_headers['x-qumail-signature']
            if 'x-qumail-quantum-enhancement' in custom_headers:
                try:
                    metadata['quantum_enhancement'] = json.loads(custom_headers['x-qumail-quantum-enhancement'])
                except (json.JSONDecodeError, TypeError):
                    metadata['quantum_enhancement'] = {'enabled': False}

            # Extract Level 4 RSA-specific headers
            if 'x-qumail-encrypted-session-key' in custom_headers:
                metadata['encrypted_session_key'] = custom_headers['x-qumail-encrypted-session-key']
            if 'x-qumail-iv' in custom_headers:
                metadata['iv'] = custom_headers['x-qumail-iv']
            if 'x-qumail-aad' in custom_headers:
                metadata['aad'] = custom_headers['x-qumail-aad']
            if 'x-qumail-public-key' in custom_headers:
                metadata['public_key'] = custom_headers['x-qumail-public-key']
            if 'x-qumail-private-key-ref' in custom_headers:
                metadata['private_key_ref'] = custom_headers['x-qumail-private-key-ref']

            metadata['sync_type'] = 'qumail_encrypted' if is_qumail_encrypted else 'gmail_plain'
            if encryption_algorithm:
                metadata['algorithm'] = encryption_algorithm
            if security_level:
                metadata['security_level'] = security_level
            if encryption_key_id:
                metadata['key_id'] = encryption_key_id
            if flow_id:
                metadata['flow_id'] = flow_id
            if sender_name:
                metadata['senderName'] = sender_name
            if receiver_name:
                metadata['receiverName'] = receiver_name

            # If this flow already exists, update metadata/Gmail ID and return the existing record
            existing_flow = await email_repo.find_by_flow_id(flow_id)
            if existing_flow:
                existing_meta = existing_flow.encryption_metadata or {}
                if isinstance(existing_meta, str):
                    try:
                        existing_meta = json.loads(existing_meta)
                    except json.JSONDecodeError:
                        existing_meta = {'raw_metadata': existing_meta}

                merged_meta = dict(existing_meta)
                merged_meta.update(metadata)
                if isinstance(existing_meta.get('key_ids'), dict) or isinstance(metadata.get('key_ids'), dict):
                    merged_meta['key_ids'] = {
                        **(existing_meta.get('key_ids') or {}),
                        **(metadata.get('key_ids') or {})
                    }
                if metadata.get('key_fragments'):
                    merged_meta['key_fragments'] = metadata['key_fragments']

                merged_allowed: Set[str] = set(existing_flow.allowed_emails or [])
                merged_allowed.update(allowed_email_set)

                updates: Dict[str, Any] = {
                    "gmail_message_id": gmail_message_id,
                    "encryption_metadata": merged_meta,
                    "sender_email": existing_flow.sender_email or sender_email,
                    "receiver_email": existing_flow.receiver_email or receiver_email,
                    "encryption_key_id": existing_flow.encryption_key_id or encryption_key_id,
                    "encryption_iv": existing_flow.encryption_iv or metadata.get('nonce') or existing_meta.get('nonce'),
                    "encryption_auth_tag": existing_flow.encryption_auth_tag or metadata.get('auth_tag') or existing_meta.get('auth_tag')
                }
                if merged_allowed:
                    updates["allowed_emails"] = sorted(merged_allowed)
                await email_repo.update(existing_flow.id, updates)
                logger.info(
                    "Flow %s already stored; metadata refreshed and Gmail ID linked",
                    flow_id
                )
                return await email_repo.find_by_id(existing_flow.id)

            timestamp = datetime.utcnow()
            timestamp_str = gmail_msg.get('timestamp')
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                except Exception:
                    pass

            body_content = body_html or body_text or ''

            email_doc = EmailDocument(
                flow_id=flow_id,
                user_id=str(user_id),
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
                encryption_iv=metadata.get('nonce'),
                encryption_auth_tag=metadata.get('auth_tag'),
                encryption_metadata=metadata,
                allowed_emails=allowed_email_list
            )

            await email_repo.create(email_doc)
            logger.info(
                "Stored Gmail message %s locally (security_level=%s)",
                gmail_message_id,
                security_level
            )
            return email_doc

        except Exception as e:
            logger.error(f"Failed to persist Gmail message locally: {e}")
            return None
    
    async def sync_gmail_encrypted_emails(
        self,
        user_email: str,
        gmail_credentials: Dict,
        db: Any
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

            for gmail_msg in gmail_messages:
                stored_email = await self.store_gmail_message_locally(
                    gmail_msg=gmail_msg,
                    user_email=user.email,
                    user_id=str(user.id),
                    db=db
                )

                if not stored_email:
                    continue

                synced_total += 1
                if stored_email.security_level:
                    encrypted_synced += 1

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
