"""
Complete Email API Routes with Real Quantum Encryption
All endpoints properly integrated with KMS and encryption services
"""
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, EmailStr
from typing import Optional, List
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

class DecryptEmailResponse(BaseModel):
    success: bool
    email_id: str
    subject: str
    body: str
    from_email: str
    to_email: str
    timestamp: str
    security_level: int

class KeyPoolStatusResponse(BaseModel):
    total_keys: int
    available_keys: int
    in_use_keys: int
    consumed_keys: int
    average_entropy: float
    pool_health: str

# NOTE: Use get_current_user from app.api.auth to ensure consistent auth across routes

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

        # Ensure user has access (sender, receiver, or owner)
        if (
            email.sender_email != current_user.email
            and email.receiver_email != current_user.email
            and email.user_id != str(current_user.id)
        ):
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
                logger.warning(
                    "Gmail message %s has no associated encrypted metadata for %s",
                    gmail_message_id,
                    current_user.email,
                )
                raise HTTPException(
                    status_code=404,
                    detail="Encrypted metadata for this Gmail message is unavailable in QuMail. Ensure it was sent via QuMail and sync again.",
                )
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

        if (
            email_doc.sender_email != current_user.email
            and email_doc.receiver_email != current_user.email
            and email_doc.user_id != str(current_user.id)
        ):
            raise HTTPException(status_code=403, detail="Access denied")

        result = await complete_email_service.receive_and_decrypt_email(
            email_id=resolved_email_id,
            db=db
        )
        
        return DecryptEmailResponse(
            success=result['success'],
            email_id=str(result['email_id']),
            subject=result['subject'],
            body=result['body'],
            from_email=result['from'],
            to_email=result['to'],
            timestamp=result['timestamp'],
            security_level=result['security_level']
        )
        
    except Exception as e:
        logger.error(f"Error decrypting email {email_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to decrypt email: {str(e)}"
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
        
        status = await quantum_key_pool.get_pool_status()
        
        return {
            'success': True,
            'message': 'Quantum key pool initialized successfully',
            'pool_status': status
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
        status = await kme_service.get_system_status()
        
        return {
            'success': True,
            'kme_status': status
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
