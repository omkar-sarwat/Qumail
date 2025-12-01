"""
Complete Email API Routes with Real Quantum Encryption
All endpoints properly integrated with KMS and encryption services
"""
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
import logging
import json

from ..mongo_database import get_database
from ..mongo_models import UserDocument
from ..mongo_repositories import EmailRepository
from ..api.auth import get_current_user  # Use centralized auth that honors Authorization header and test token
from ..services.complete_email_service import complete_email_service
from ..services.encryption.quantum_key_pool import quantum_key_pool
from ..services.kme_service import kme_service
from ..services.gmail_service import gmail_service
from ..services.gmail_oauth import oauth_service
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/emails", tags=["emails"])

# Request/Response Models
class SendEmailRequest(BaseModel):
    to: EmailStr
    subject: str
    body: str
    security_level: int  # 1-4
    cc: Optional[str] = None
    bcc: Optional[str] = None

class SendEmailResponse(BaseModel):
    success: bool
    email_id: str
    flow_id: str
    encryption_details: dict
    message: str

class EmailListResponse(BaseModel):
    emails: List[dict]
    total: int
    folder: str

class DecryptedEmailData(BaseModel):
    email_id: str
    subject: Optional[str] = None
    body: str
    sender_email: Optional[str] = None
    receiver_email: Optional[str] = None
    timestamp: Optional[str] = None
    flow_id: Optional[str] = None
    key_id: Optional[str] = None
    security_level: int = 0
    algorithm: Optional[str] = None
    verification_status: Optional[str] = "Verified"
    quantum_enhanced: bool = True
    encrypted_size: Optional[int] = None
    attachments: Optional[List[Dict[str, Any]]] = None

class SecurityInfo(BaseModel):
    security_level: int
    algorithm: Optional[str] = None
    verification_status: str = "Verified"
    quantum_enhanced: bool = True
    encrypted_size: Optional[int] = None

class DecryptEmailResponse(BaseModel):
    success: bool
    message: str = "Email decrypted successfully"
    email_data: DecryptedEmailData
    security_info: SecurityInfo

class KeyPoolStatusResponse(BaseModel):
    total_keys: int
    available_keys: int
    in_use_keys: int
    consumed_keys: int
    average_entropy: float
    pool_health: str

# Request model for direct decryption (no MongoDB)
class DirectDecryptRequest(BaseModel):
    """Decrypt using headers/metadata passed from frontend - no MongoDB needed"""
    ciphertext: str  # Base64 encoded encrypted content
    flow_id: str
    key_id: Optional[str] = None
    key_fragments: Optional[List[str]] = None
    security_level: int = 1
    algorithm: Optional[str] = None
    auth_tag: Optional[str] = None
    nonce: Optional[str] = None
    salt: Optional[str] = None
    plaintext_size: Optional[int] = None
    subject: Optional[str] = None
    sender_email: Optional[str] = None
    # Level 3 PQC-specific fields
    kem_ciphertext: Optional[str] = None
    kem_secret_key: Optional[str] = None
    kem_public_key: Optional[str] = None
    dsa_public_key: Optional[str] = None
    signature: Optional[str] = None
    quantum_enhancement: Optional[Dict[str, Any]] = None
    # Legacy aliases for backward compatibility
    kyber_ciphertext: Optional[str] = None
    kyber_private_key: Optional[str] = None
    dilithium_public_key: Optional[str] = None

# NOTE: Use get_current_user from app.api.auth to ensure consistent auth across routes

@router.post("/decrypt-direct", response_model=DecryptEmailResponse)
async def decrypt_email_direct(
    request: DirectDecryptRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserDocument = Depends(get_current_user)
):
    """
    Decrypt email using headers/metadata passed from frontend.
    No MongoDB lookup - all data comes from Gmail headers.
    One-time decrypt - frontend should cache the result locally.
    """
    try:
        logger.info(f"Direct decrypt request for flow_id={request.flow_id}, level={request.security_level}")
        
        # Build metadata from request
        metadata = {
            'flow_id': request.flow_id,
            'key_id': request.key_id,
            'key_fragments': request.key_fragments or ([request.key_id] if request.key_id else []),
            'algorithm': request.algorithm or f"Level{request.security_level}",
            'auth_tag': request.auth_tag,
            'nonce': request.nonce,
            'salt': request.salt,
            'required_size': request.plaintext_size,
        }
        
        # Add Level 3 PQC-specific fields if present
        if request.security_level == 3:
            # Support both new (kem_*) and legacy (kyber_*) field names
            metadata['kem_ciphertext'] = request.kem_ciphertext or request.kyber_ciphertext
            metadata['kem_secret_key'] = request.kem_secret_key or request.kyber_private_key
            metadata['kem_public_key'] = request.kem_public_key
            metadata['dsa_public_key'] = request.dsa_public_key or request.dilithium_public_key
            metadata['signature'] = request.signature
            metadata['quantum_enhancement'] = request.quantum_enhancement or {'enabled': False}
            # Also set legacy aliases for backward compatibility
            if request.kem_ciphertext:
                metadata['kyber_ciphertext'] = request.kem_ciphertext
            if request.kem_secret_key:
                metadata['kyber_private_key'] = request.kem_secret_key
        
        # Decrypt based on security level
        encryption_service = complete_email_service.encryption_service
        
        if request.security_level == 1:
            decrypted_bytes = await encryption_service.decrypt_level_1_otp(
                request.ciphertext,
                metadata,
                current_user.email
            )
        elif request.security_level == 2:
            decrypted_bytes = await encryption_service.decrypt_level_2_aes(
                request.ciphertext,
                metadata,
                current_user.email
            )
        elif request.security_level == 3:
            decrypted_bytes = await encryption_service.decrypt_level_3_pqc(
                request.ciphertext,
                metadata,
                current_user.email
            )
        elif request.security_level == 4:
            decrypted_bytes = await encryption_service.decrypt_level_4_standard(
                request.ciphertext,
                metadata,
                current_user.email
            )
        else:
            raise HTTPException(status_code=400, detail=f"Invalid security level: {request.security_level}")
        
        # Parse decrypted content
        decrypted_text = decrypted_bytes.decode('utf-8') if isinstance(decrypted_bytes, bytes) else decrypted_bytes
        
        # Try to parse as JSON (structured message)
        try:
            message_data = json.loads(decrypted_text)
            body = message_data.get('body', decrypted_text)
            subject = message_data.get('subject', request.subject)
        except json.JSONDecodeError:
            body = decrypted_text
            subject = request.subject
        
        algorithm_names = {
            1: "Quantum-Aided OTP",
            2: "Quantum-Aided AES-256",
            3: "PQC-Kyber1024",
            4: "RSA-4096-Hybrid"
        }
        
        # Get key_id from request or key_fragments
        resolved_key_id = request.key_id or (request.key_fragments[0] if request.key_fragments else request.flow_id)
        
        return DecryptEmailResponse(
            success=True,
            message="Email decrypted successfully",
            email_data=DecryptedEmailData(
                email_id=request.flow_id,
                subject=subject,
                body=body,
                sender_email=request.sender_email,
                receiver_email=current_user.email,
                timestamp=datetime.utcnow().isoformat(),
                flow_id=request.flow_id,
                key_id=resolved_key_id,
                security_level=request.security_level,
                algorithm=algorithm_names.get(request.security_level, "Unknown"),
                verification_status="Verified",
                quantum_enhanced=True,
                encrypted_size=len(request.ciphertext)
            ),
            security_info=SecurityInfo(
                security_level=request.security_level,
                algorithm=algorithm_names.get(request.security_level, "Unknown"),
                verification_status="Verified",
                quantum_enhanced=True,
                encrypted_size=len(request.ciphertext)
            )
        )
        
    except Exception as e:
        logger.error(f"Direct decryption failed: {e}")
        raise HTTPException(status_code=400, detail=f"Decryption failed: {str(e)}")

@router.post("/send", response_model=SendEmailResponse)
async def send_encrypted_email(
    request: SendEmailRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserDocument = Depends(get_current_user)
):
    """
    Send encrypted email with specified security level
    
    Security Levels:
    - 1: Quantum One-Time Pad (Perfect Secrecy)
    - 2: Quantum-Aided AES-256-GCM
    - 3: Post-Quantum Cryptography
    - 4: Standard RSA-2048
    """
    try:
        # Validate security level
        if request.security_level not in [1, 2, 3, 4]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid security level. Must be 1-4."
            )
        
        # Get Gmail credentials from current user (if available)
        gmail_credentials = None
        if current_user.oauth_access_token:
            gmail_credentials = {
                'access_token': current_user.oauth_access_token,
                'refresh_token': current_user.oauth_refresh_token,
                'token_expiry': current_user.oauth_token_expiry
            }
        
        # Send encrypted email
        result = await complete_email_service.send_encrypted_email(
            sender_email=current_user.email,
            sender_user_id=current_user.id,  # MongoDB user ID used for access control
            recipient_email=request.to,
            subject=request.subject,
            body=request.body,
            security_level=request.security_level,
            cc=request.cc,
            bcc=request.bcc,
            db=db,
            gmail_credentials=gmail_credentials
        )
        
        return SendEmailResponse(
            success=result['success'],
            email_id=str(result['email_id']),
            flow_id=result['flow_id'],
            encryption_details=result['encryption_details'],
            message=f"Email encrypted and sent successfully with security level {request.security_level}"
        )
        
    except Exception as e:
        logger.error(f"Error sending encrypted email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send encrypted email: {str(e)}"
        )

@router.get("/inbox", response_model=EmailListResponse)
async def get_inbox_emails(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserDocument = Depends(get_current_user)
):
    """Get real Gmail inbox emails using Mongo-backed OAuth tokens."""
    try:
        if not current_user.oauth_access_token:
            raise HTTPException(status_code=401, detail="Gmail account not connected")

        access_token = await oauth_service.get_valid_access_token(current_user.email, db)
        result = await gmail_service.fetch_emails(
            access_token=access_token,
            folder="INBOX",
            max_results=50
        )
        emails = result.get("emails", [])
        return EmailListResponse(
            emails=emails,
            total=result.get("total_count", len(emails)),
            folder="inbox"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Gmail inbox emails: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch Gmail inbox: {str(e)}"
        )

@router.get("/sent", response_model=EmailListResponse)
async def get_sent_emails(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserDocument = Depends(get_current_user)
):
    """Get Gmail sent emails (real data only)."""
    try:
        if not current_user.oauth_access_token:
            raise HTTPException(status_code=401, detail="Gmail account not connected")

        access_token = await oauth_service.get_valid_access_token(current_user.email, db)
        result = await gmail_service.fetch_emails(
            access_token=access_token,
            folder="SENT",
            max_results=50
        )
        emails = result.get("emails", [])
        return EmailListResponse(
            emails=emails,
            total=result.get("total_count", len(emails)),
            folder='sent'
        )
    except Exception as e:
        logger.error(f"Error getting Gmail sent emails: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get Gmail sent emails: {str(e)}"
        )

@router.get("/email/{email_id}")
async def get_email_details(
    email_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserDocument = Depends(get_current_user)
):
    """
    Get email details by ID
    Returns email metadata and content
    """
    try:
        if email_id.startswith("gmail_"):
            if not current_user.oauth_access_token:
                raise HTTPException(status_code=401, detail="Gmail account not connected")
            access_token = await oauth_service.get_valid_access_token(current_user.email, db)
            email_details = await gmail_service.get_email_by_id(access_token, email_id)
            if not email_details:
                raise HTTPException(status_code=404, detail="Email not found")
            return email_details
        email_repo = EmailRepository(db)
        email = await email_repo.find_by_id(email_id)
        if not email:
            email = await email_repo.find_by_flow_id(email_id)
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")

        # Ensure user has access (sender, receiver, or owner) - case insensitive comparison
        user_email_lower = current_user.email.lower() if current_user.email else ""
        sender_lower = (email.sender_email or "").lower()
        receiver_lower = (email.receiver_email or "").lower()
        user_id_str = str(current_user.id) if current_user.id else ""
        
        has_access = (
            sender_lower == user_email_lower or
            receiver_lower == user_email_lower or
            email.user_id == user_id_str
        )
        
        if not has_access:
            logger.warning(
                f"Access denied for email {email_id}: sender={email.sender_email}, "
                f"receiver={email.receiver_email}, user_id={email.user_id}, "
                f"current_user={current_user.email}, current_user_id={current_user.id}"
            )
            raise HTTPException(status_code=403, detail="Access denied")

        metadata = email.encryption_metadata or {}
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except json.JSONDecodeError:
                metadata = {"raw_metadata": metadata}

        response = {
            "email_id": email.id,
            "flow_id": email.flow_id,
            "sender_email": email.sender_email,
            "receiver_email": email.receiver_email,
            "subject": email.subject,
            "body_encrypted": email.body_encrypted,
            "security_level": email.security_level,
            "timestamp": email.timestamp.isoformat(),
            "is_read": email.is_read,
            "is_starred": email.is_starred,
            "is_suspicious": email.is_suspicious,
            "encryption_metadata": metadata,
            "requires_decryption": email.security_level in {1, 2, 3, 4} and not email.decrypted_body,
            "source": metadata.get("source", "qumail"),
        }

        # If already decrypted, include the plaintext body
        if email.decrypted_body:
            try:
                decrypted_data = json.loads(email.decrypted_body)
                response["body"] = decrypted_data.get("body", "")
                response["decrypted_content"] = decrypted_data
                response["is_decrypted"] = True
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse decrypted_body for email {email.id}")

        if metadata.get("bodyText"):
            response["body"] = metadata.get("bodyText")

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting email details {email_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get email details: {str(e)}"
        )

@router.get("/email/{email_id}/decrypt", response_model=DecryptEmailResponse)
@router.post("/email/{email_id}/decrypt", response_model=DecryptEmailResponse)
async def decrypt_email(
    email_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserDocument = Depends(get_current_user)
):
    """
    Decrypt email - ONLY accessible in QuMail app
    Returns plaintext content
    """
    try:
        email_repo = EmailRepository(db)
        resolved_email_id = email_id
        email_doc = None

        if email_id.startswith("gmail_"):
            gmail_message_id = email_id.replace("gmail_", "", 1)
            email_doc = await email_repo.find_by_gmail_id(gmail_message_id)
            if not email_doc:
                # Try to fetch the email from Gmail and extract encryption metadata
                logger.info(
                    "Gmail message %s has no stored metadata, attempting to extract from Gmail body...",
                    gmail_message_id,
                )
                try:
                    # Get a valid OAuth access token (will auto-refresh if expired)
                    try:
                        access_token = await oauth_service.get_valid_access_token(
                            user_email=current_user.email,
                            session=db
                        )
                        logger.info("Got valid access token for user %s", current_user.email)
                    except Exception as token_error:
                        logger.error("Failed to get valid access token: %s", token_error)
                        raise HTTPException(
                            status_code=401,
                            detail="OAuth token expired or invalid. Please re-authenticate with Google."
                        )
                    
                    # Fetch email from Gmail
                    gmail_email = await gmail_service.get_email_by_id(
                        access_token=access_token,
                        email_id=gmail_message_id
                    )
                    
                    if gmail_email:
                        import re
                        
                        # FIRST: Try to extract from X-QuMail headers (most reliable)
                        custom_headers = gmail_email.get('customHeaders', {})
                        
                        flow_id = custom_headers.get('x-qumail-flow-id', '')
                        key_id = custom_headers.get('x-qumail-key-id', '')
                        security_level_header = custom_headers.get('x-qumail-security-level', '')
                        algorithm = custom_headers.get('x-qumail-algorithm', '')
                        auth_tag = custom_headers.get('x-qumail-auth-tag', '')
                        nonce = custom_headers.get('x-qumail-nonce', '')
                        salt = custom_headers.get('x-qumail-salt', '')
                        plaintext_size = custom_headers.get('x-qumail-plaintext-size', '')
                        key_fragments = custom_headers.get('x-qumail-key-fragments', '')
                        key_ids_header = custom_headers.get('x-qumail-key-ids', '')
                        
                        if flow_id:
                            logger.info(
                                "Found encryption metadata in X-QuMail headers: flow_id=%s, key_id=%s, level=%s",
                                flow_id, key_id, security_level_header
                            )
                        
                        # SECOND: Fall back to body parsing if headers not found
                        body_content = gmail_email.get('body', '') or gmail_email.get('bodyHtml', '') or ''
                        
                        # Log the body for debugging
                        logger.info("Attempting to extract encryption metadata from Gmail body (%d chars)", len(body_content))
                        
                        # Check if this is a QuMail encrypted email
                        is_qumail_email = (
                            flow_id or  # Headers found
                            'quantum-encrypted' in body_content.lower() or
                            'qumail' in body_content.lower() or
                            'encryption details' in body_content.lower() or
                            'flow id' in body_content.lower()
                        )
                        
                        if not is_qumail_email:
                            logger.warning("Email does not appear to be a QuMail encrypted message")
                            raise HTTPException(
                                status_code=400,
                                detail="This email is not a QuMail encrypted message. Only emails sent via QuMail can be decrypted."
                            )
                        
                        # If not from headers, parse flow_id from body
                        if not flow_id:
                            flow_id_match = (
                                re.search(r'<strong>Flow ID:</strong>\s*([a-f0-9-]+)', body_content, re.IGNORECASE) or
                                re.search(r'Flow ID[:\s]+([a-f0-9-]+)', body_content, re.IGNORECASE) or
                                re.search(r'flow_id["\s:]+([a-f0-9-]+)', body_content, re.IGNORECASE)
                            )
                            if flow_id_match:
                                flow_id = flow_id_match.group(1)
                        
                        if not key_id:
                            key_id_match = (
                                re.search(r'<strong>Key ID:</strong>\s*([a-f0-9-]+)', body_content, re.IGNORECASE) or
                                re.search(r'Key ID[:\s]+([a-f0-9-]+)', body_content, re.IGNORECASE) or
                                re.search(r'key_id["\s:]+([a-f0-9-]+)', body_content, re.IGNORECASE)
                            )
                            if key_id_match:
                                key_id = key_id_match.group(1)
                        
                        # Extract ciphertext - look for the div containing ciphertext
                        cipher_match = None
                        
                        # Pattern 1: Look for content after "ENCRYPTED CONTENT (BASE64 CIPHERTEXT)" marker
                        cipher_pattern1 = re.search(
                            r'BASE64 CIPHERTEXT[^<]*</div>\s*<div[^>]*>([A-Za-z0-9+/=\s\n]+)</div>',
                            body_content, re.IGNORECASE | re.DOTALL
                        )
                        
                        # Pattern 2: Look for monospace div with ciphertext
                        cipher_pattern2 = re.search(
                            r'monospace[^>]*>([A-Za-z0-9+/=\s\n]{20,})</div>',
                            body_content, re.IGNORECASE | re.DOTALL
                        )
                        
                        # Pattern 3: Look for large base64 block
                        cipher_pattern3 = re.search(
                            r'([A-Za-z0-9+/]{100,}={0,2})',
                            body_content
                        )
                        
                        # Pattern 4: Plain text format
                        cipher_pattern4 = re.search(
                            r'ENCRYPTED CONTENT \(BASE64\):\s*\n([A-Za-z0-9+/=\s\n]+)',
                            body_content, re.IGNORECASE
                        )
                        
                        cipher_match = cipher_pattern1 or cipher_pattern2 or cipher_pattern3 or cipher_pattern4
                        
                        # Extract security level - prefer header, then body
                        security_level = 1  # Default to OTP
                        if security_level_header:
                            try:
                                security_level = int(security_level_header)
                            except ValueError:
                                pass
                        else:
                            level_match = re.search(r'Security Level[:\s]*(\d)', body_content, re.IGNORECASE)
                            if level_match:
                                security_level = int(level_match.group(1))
                            elif 'level 2' in body_content.lower() or 'aes-256' in body_content.lower():
                                security_level = 2
                            elif 'level 3' in body_content.lower() or 'pqc' in body_content.lower() or 'kyber' in body_content.lower():
                                security_level = 3
                            elif 'level 4' in body_content.lower() or 'rsa' in body_content.lower():
                                security_level = 4
                        
                        logger.info(
                            "Extraction results - Flow ID: %s, Key ID: %s, Cipher: %s, Level: %d",
                            flow_id if flow_id else "NOT FOUND",
                            key_id if key_id else "NOT FOUND",
                            "found" if cipher_match else "NOT FOUND",
                            security_level
                        )
                        
                        # FIRST: If we have a flow_id, check if document already exists in MongoDB
                        # This handles the case where sender already created the receiver's document
                        if flow_id:
                            existing_doc = await email_repo.find_by_flow_id(flow_id)
                            if existing_doc:
                                # Document already exists - use it directly, no need for ciphertext extraction
                                email_doc = existing_doc
                                resolved_email_id = existing_doc.id
                                logger.info(
                                    "Found existing email document with flow_id %s - using it for decryption (skipping Gmail extraction)",
                                    flow_id
                                )
                            elif cipher_match:
                                # No existing doc, but we have ciphertext - create new document
                                ciphertext = cipher_match.group(1).replace('\n', '').replace(' ', '').replace('\r', '').strip()
                                
                                logger.info(
                                    "No existing document found. Creating from extracted data: flow_id=%s, key_id=%s, ciphertext_len=%d",
                                    flow_id, key_id, len(ciphertext)
                                )
                                
                                # Parse key fragments if available
                                parsed_key_fragments = None
                                if key_fragments:
                                    try:
                                        import json
                                        parsed_key_fragments = json.loads(key_fragments)
                                    except:
                                        try:
                                            parsed_key_fragments = [x.strip() for x in key_fragments.split(',') if x.strip()]
                                        except:
                                            pass
                                
                                # Parse key IDs if available
                                parsed_key_ids = None
                                if key_ids_header:
                                    try:
                                        import json
                                        parsed_key_ids = json.loads(key_ids_header)
                                    except:
                                        pass
                                
                                # Create new email document for decryption
                                from ..mongo_models import EmailDocument, EmailDirection
                                import uuid
                                
                                temp_email_id = str(uuid.uuid4())
                                email_doc = EmailDocument(
                                    id=temp_email_id,
                                    flow_id=flow_id,
                                    user_id=str(current_user.id),
                                    sender_email=gmail_email.get('sender', '') or gmail_email.get('from', ''),
                                    receiver_email=current_user.email,
                                    subject=gmail_email.get('subject', ''),
                                    body_encrypted=ciphertext,
                                    encryption_key_id=key_id,
                                    security_level=security_level,
                                    direction=EmailDirection.RECEIVED,
                                    gmail_message_id=gmail_message_id,
                                    encryption_metadata={
                                        'flow_id': flow_id,
                                        'key_id': key_id,
                                        'algorithm': algorithm or f"Level{security_level}",
                                        'auth_tag': auth_tag,
                                        'nonce': nonce,
                                        'salt': salt,
                                        'plaintext_size': int(plaintext_size) if plaintext_size else None,
                                        'key_fragments': parsed_key_fragments,
                                        'key_ids': parsed_key_ids,
                                        'extracted_from_gmail': True,
                                        'extracted_from_headers': bool(custom_headers.get('x-qumail-flow-id'))
                                    }
                                )
                                
                                # Save to database for future use
                                await email_repo.create(email_doc)
                                resolved_email_id = temp_email_id
                                logger.info(
                                    "Created email document %s from Gmail message %s with extracted metadata",
                                    temp_email_id,
                                    gmail_message_id,
                                )
                            else:
                                # Have flow_id but no existing doc and no ciphertext
                                logger.warning(
                                    "Found flow_id %s but no existing document and couldn't extract ciphertext",
                                    flow_id
                                )
                                raise HTTPException(
                                    status_code=400,
                                    detail="Found encryption metadata but couldn't extract encrypted content. The email document may have been deleted."
                                )
                        else:
                            logger.warning(
                                "Could not extract flow_id or ciphertext from Gmail message %s",
                                gmail_message_id,
                            )
                            raise HTTPException(
                                status_code=400,
                                detail="Could not extract encryption metadata from email. The email may not be a valid QuMail encrypted message."
                            )
                    else:
                        raise HTTPException(
                            status_code=404,
                            detail="Could not fetch email from Gmail."
                        )
                except HTTPException:
                    raise
                except Exception as extract_error:
                    logger.error(f"Error extracting metadata from Gmail: {extract_error}")
                    raise HTTPException(
                        status_code=400,
                        detail=f"Failed to extract encryption metadata: {str(extract_error)}"
                    )
            else:
                resolved_email_id = email_doc.id
                logger.info(
                    "Resolved Gmail message %s to stored email %s for decrypt",
                    gmail_message_id,
                    resolved_email_id,
                )
        else:
            email_doc = await email_repo.find_by_id(resolved_email_id)
            if not email_doc:
                email_doc = await email_repo.find_by_flow_id(resolved_email_id)
                if email_doc:
                    resolved_email_id = email_doc.id

        if not email_doc:
            raise HTTPException(status_code=404, detail="Email not found")

        # Ensure user has access (sender, receiver, or owner) - case insensitive comparison
        user_email_lower = current_user.email.lower() if current_user.email else ""
        sender_lower = (email_doc.sender_email or "").lower()
        receiver_lower = (email_doc.receiver_email or "").lower()
        user_id_str = str(current_user.id) if current_user.id else ""
        
        has_access = (
            sender_lower == user_email_lower or
            receiver_lower == user_email_lower or
            email_doc.user_id == user_id_str
        )
        
        if not has_access:
            logger.warning(
                f"Decrypt access denied for email {email_id}: sender={email_doc.sender_email}, "
                f"receiver={email_doc.receiver_email}, user_id={email_doc.user_id}, "
                f"current_user={current_user.email}, current_user_id={current_user.id}"
            )
            raise HTTPException(status_code=403, detail="Access denied")

        result = await complete_email_service.receive_and_decrypt_email(
            email_id=resolved_email_id,
            db=db
        )
        
        # Get algorithm name for display
        algorithm_names = {
            1: "OTP-QKD-ETSI-014",
            2: "AES-256-GCM-QKD",
            3: "PQC-Kyber1024",
            4: "RSA-4096-Hybrid"
        }
        algorithm = algorithm_names.get(result.get('security_level', 0), result.get('algorithm', 'Unknown'))
        
        # Build nested response structure
        # Get encrypted_size safely - it might not exist on the document
        encrypted_size = None
        if email_doc:
            encrypted_size = getattr(email_doc, 'encrypted_size', None)
            if encrypted_size is None and email_doc.body_encrypted:
                encrypted_size = len(email_doc.body_encrypted)
        
        email_data = DecryptedEmailData(
            email_id=str(result['email_id']),
            subject=result.get('subject'),
            body=result.get('body', ''),
            sender_email=result.get('from'),
            receiver_email=result.get('to'),
            timestamp=result.get('timestamp'),
            flow_id=result.get('flow_id'),
            key_id=result.get('key_id') or result.get('flow_id'),
            security_level=result.get('security_level', 0),
            algorithm=algorithm,
            verification_status="Verified" if result.get('success') else "Failed",
            quantum_enhanced=result.get('security_level', 0) in [1, 2, 3],
            encrypted_size=encrypted_size,
            attachments=result.get('attachments', [])
        )
        
        security_info = SecurityInfo(
            security_level=result.get('security_level', 0),
            algorithm=algorithm,
            verification_status="Verified" if result.get('success') else "Failed",
            quantum_enhanced=result.get('security_level', 0) in [1, 2, 3],
            encrypted_size=encrypted_size
        )
        
        return DecryptEmailResponse(
            success=result['success'],
            message="Email decrypted successfully" if result['success'] else "Decryption failed",
            email_data=email_data,
            security_info=security_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e) if str(e) else "Unknown error occurred"
        logger.error(f"Error decrypting email {email_id}: {error_msg}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to decrypt email: {error_msg}"
        )

@router.post("/sync/gmail")
async def sync_gmail_emails(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserDocument = Depends(get_current_user)
):
    """Sync encrypted emails from Gmail"""
    try:
        # Get Gmail credentials from current user
        if not current_user.oauth_access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No Gmail OAuth credentials found. Please authenticate with Google first."
            )
        
        gmail_credentials = {
            'access_token': current_user.oauth_access_token,
            'refresh_token': current_user.oauth_refresh_token,
            'token_expiry': current_user.oauth_token_expiry
        }
        
        result = await complete_email_service.sync_gmail_encrypted_emails(
            user_email=current_user.email,
            gmail_credentials=gmail_credentials,
            db=db
        )
        
        return {
            'success': result['success'],
            'synced_count': result['synced_count'],
            'total_messages': result['total_messages'],
            'message': f"Synced {result['synced_count']} encrypted emails from Gmail"
        }
        
    except Exception as e:
        logger.error(f"Error syncing Gmail emails: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync Gmail emails: {str(e)}"
        )

@router.get("/quantum/pool/status", response_model=KeyPoolStatusResponse)
async def get_key_pool_status():
    """Get status of quantum key pool"""
    try:
        status = await quantum_key_pool.get_pool_status()
        
        return KeyPoolStatusResponse(
            total_keys=status['total_keys'],
            available_keys=status['available_keys'],
            in_use_keys=status['in_use_keys'],
            consumed_keys=status['consumed_keys'],
            average_entropy=status['average_entropy'],
            pool_health=status['pool_health']
        )
        
    except Exception as e:
        logger.error(f"Error getting key pool status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get key pool status: {str(e)}"
        )

@router.post("/quantum/pool/initialize")
async def initialize_key_pool():
    """Initialize quantum key pool with keys from KME1"""
    try:
        await quantum_key_pool.initialize_pool(kme_service)
        
        pool_status = await quantum_key_pool.get_pool_status()
        
        return {
            'success': True,
            'message': 'Quantum key pool initialized successfully',
            'pool_status': pool_status
        }
        
    except Exception as e:
        logger.error(f"Error initializing key pool: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize key pool: {str(e)}"
        )

@router.get("/quantum/kme/status")
async def get_kme_status():
    """Get status of KME servers"""
    try:
        kme_status = await kme_service.get_system_status()
        
        return {
            'success': True,
            'kme_status': kme_status
        }
        
    except Exception as e:
        logger.error(f"Error getting KME status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get KME status: {str(e)}"
        )

@router.post("/quantum/keys/generate")
async def generate_quantum_keys(count: int = 10):
    """Generate new quantum keys and add to pool"""
    try:
        # Generate keys from KME1
        keys = await kme_service.generate_keys(kme_id=1, count=count)
        
        return {
            'success': True,
            'generated_count': len(keys),
            'message': f'Generated {len(keys)} quantum keys'
        }
        
    except Exception as e:
        logger.error(f"Error generating quantum keys: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate quantum keys: {str(e)}"
        )
