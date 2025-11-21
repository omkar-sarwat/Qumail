from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from fastapi.responses import RedirectResponse
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Optional, Dict, Any
import logging
from ..mongo_database import get_database
from ..services.gmail_oauth import oauth_service, OAuthError, TokenError
from ..services.gmail_client import gmail_client, GmailError
from ..services.security_auditor import security_auditor, SecurityIncidentType
from ..schemas import SecurityLevel
from ..request_schemas import (
    SendEmailRequest, 
    GetMessagesRequest,
    MessageActionRequest
)
from ..response_schemas import (
    AuthURLResponse,
    OAuthCallbackResponse,
    MessageListResponse,
    MessageDetailResponse,
    SendEmailResponse,
    UserInfoResponse
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["Gmail API"])

# OAuth Routes

@router.get("/auth/google", response_model=AuthURLResponse)
async def get_google_auth_url(
    user_id: Optional[str] = Query(None, description="Optional user ID for state tracking")
):
    """
    Get Google OAuth authorization URL
    
    Security Features:
    - CSRF protection with state parameter
    - PKCE for additional security
    - Offline access for refresh tokens
    """
    try:
        auth_data = oauth_service.generate_authorization_url(user_id)
        
        logger.info(f"Generated OAuth URL for user: {user_id}")
        
        return AuthURLResponse(
            authorization_url=auth_data["authorization_url"],
            state=auth_data["state"],
            message="Visit the authorization URL to grant access to Gmail"
        )
    
    except Exception as e:
        logger.error(f"Error generating OAuth URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate authorization URL"
        )

@router.get("/auth/google/callback", response_model=OAuthCallbackResponse)
async def google_oauth_callback(
    code: str = Query(..., description="Authorization code from Google"),
    state: str = Query(..., description="State parameter for CSRF protection"),
    error: Optional[str] = Query(None, description="OAuth error if any"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Handle Google OAuth callback
    
    Security Features:
    - State parameter validation (CSRF protection)
    - Secure token exchange
    - Encrypted token storage
    """
    # Check for OAuth errors
    if error:
        await security_auditor.log_incident(
            SecurityIncidentType.AUTH_FAILURE,
            f"OAuth callback error: {error}",
            details={"error": error, "state": state}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth authorization failed: {error}"
        )
    
    try:
        # Exchange code for tokens
        token_data = await oauth_service.exchange_code_for_tokens(code, state, db)
        
        logger.info(f"OAuth successful for user: {token_data['user_email']}")
        
        return OAuthCallbackResponse(
            success=True,
            user_email=token_data["user_email"],
            display_name=token_data["display_name"],
            session_token=token_data["session_token"],
            expires_at=token_data["expires_at"],
            message="Authentication successful"
        )
    
    except OAuthError as e:
        logger.error(f"OAuth error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except Exception as e:
        logger.error(f"Unexpected OAuth error: {e}")
        await security_auditor.log_incident(
            SecurityIncidentType.SYSTEM_ERROR,
            f"OAuth callback system error: {str(e)}",
            details={"error": str(e), "state": state}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed due to system error"
        )

@router.post("/auth/revoke")
async def revoke_tokens(
    user_email: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Revoke user's OAuth tokens"""
    try:
        await oauth_service.revoke_tokens(user_email, db)
        
        logger.info(f"Tokens revoked for user: {user_email}")
        
        return {"message": "Tokens revoked successfully"}
    
    except Exception as e:
        logger.error(f"Error revoking tokens for {user_email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke tokens"
        )

@router.get("/auth/validate")
async def validate_session(
    session_token: str = Query(..., description="Session token to validate")
):
    """Validate session token"""
    try:
        payload = oauth_service.validate_session_token(session_token)
        
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session token"
            )
        
        return {
            "valid": True,
            "user_email": payload["user_email"],
            "user_id": payload["user_id"]
        }
    
    except Exception as e:
        logger.error(f"Session validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session validation failed"
        )

# Email Routes

@router.post("/messages", response_model=MessageListResponse)
async def get_messages(
    request: GetMessagesRequest,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get Gmail messages with security validation
    
    Features:
    - Automatic token refresh
    - Security query filtering
    - Pagination support
    """
    try:
        # Validate session
        session_payload = oauth_service.validate_session_token(request.session_token)
        if not session_payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session"
            )
        
        user_email = session_payload["user_email"]
        
        # Get messages from Gmail
        result = await gmail_client.get_messages(
            user_email=user_email,
            session=db,
            query=request.query,
            max_results=request.max_results,
            page_token=request.page_token
        )
        
        # Parse message summaries
        messages = []
        for msg_summary in result.get('messages', []):
            # Get message details for display
            msg_details = await gmail_client.get_message_details(
                user_email, msg_summary['id'], db, format="metadata"
            )
            parsed_msg = gmail_client.parse_message(msg_details)
            
            messages.append({
                "id": parsed_msg["id"],
                "thread_id": parsed_msg["thread_id"],
                "subject": parsed_msg["subject"],
                "from": parsed_msg["from"],
                "date": parsed_msg["date"],
                "snippet": parsed_msg.get("snippet", ""),
                "labels": parsed_msg["labels"],
                "security_level": parsed_msg["security_level"],
                "has_attachments": parsed_msg["has_attachments"]
            })
        
        return MessageListResponse(
            messages=messages,
            next_page_token=result.get('nextPageToken'),
            result_size_estimate=result.get('resultSizeEstimate', len(messages)),
            total_messages=len(messages)
        )
    
    except GmailError as e:
        logger.error(f"Gmail API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except Exception as e:
        logger.error(f"Error fetching messages: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch messages"
        )

@router.get("/messages/{message_id}", response_model=MessageDetailResponse)
async def get_message_detail(
    message_id: str,
    session_token: str = Query(..., description="Session token"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get detailed message information"""
    try:
        # Validate session
        session_payload = oauth_service.validate_session_token(session_token)
        if not session_payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session"
            )
        
        user_email = session_payload["user_email"]
        
        # Get message details
        message_data = await gmail_client.get_message_details(
            user_email, message_id, db, format="full"
        )
        
        # Parse message
        parsed_message = gmail_client.parse_message(message_data)
        
        return MessageDetailResponse(
            **parsed_message,
            raw_size=len(str(message_data))
        )
    
    except GmailError as e:
        logger.error(f"Gmail API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except Exception as e:
        logger.error(f"Error fetching message details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch message details"
        )

@router.post("/messages/send", response_model=SendEmailResponse)
async def send_secure_email(
    request: SendEmailRequest,
    background_tasks: BackgroundTasks,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Send secure email with chosen encryption level
    
    Security Features:
    - Input validation and sanitization
    - Security level enforcement
    - Comprehensive audit logging
    """
    try:
        # Validate session
        session_payload = oauth_service.validate_session_token(request.session_token)
        if not session_payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session"
            )
        
        user_email = session_payload["user_email"]
        
        # Validate security level
        try:
            security_level = SecurityLevel(request.security_level)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid security level: {request.security_level}"
            )
        
        # Security: Apply encryption based on security level
        encrypted_body = request.body
        encryption_metadata = {}
        
        if security_level != SecurityLevel.LEVEL_4:  # All levels except plain RSA need encryption
            try:
                # Import appropriate encryption service
                if security_level == SecurityLevel.LEVEL_1:
                    from ..services.encryption.level1_otp import encrypt_otp
                    encrypted_result = await encrypt_otp(request.body, user_email)
                elif security_level == SecurityLevel.LEVEL_2:
                    from ..services.encryption.level2_aes import encrypt_aes
                    encrypted_result = await encrypt_aes(request.body, user_email)
                elif security_level == SecurityLevel.LEVEL_3:
                    from ..services.encryption.level3_pqc import encrypt_pqc
                    encrypted_result = await encrypt_pqc(request.body, user_email)
                
                encrypted_body = encrypted_result["encrypted_content"]
                encryption_metadata = encrypted_result.get("metadata", {})
                
                # Add encryption notice to subject
                request.subject = f"[QuMail {security_level.value}] {request.subject}"
                
            except Exception as e:
                logger.error(f"Encryption failed for {security_level}: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Encryption failed: {str(e)}"
                )
        
        # Send email via Gmail
        result = await gmail_client.send_message(
            user_email=user_email,
            to_addresses=request.to_addresses,
            subject=request.subject,
            body=encrypted_body,
            session=db,
            security_level=security_level,
            cc_addresses=request.cc_addresses,
            bcc_addresses=request.bcc_addresses,
            attachments=request.attachments
        )
        
        # Log security event
        background_tasks.add_task(
            security_auditor.log_incident,
            SecurityIncidentType.EMAIL_SENT,
            f"Secure email sent with {security_level.value}",
            user_id=user_email,
            details={
                "recipients": len(request.to_addresses),
                "security_level": security_level.value,
                "message_id": result["id"],
                "encryption_metadata": encryption_metadata
            }
        )
        
        logger.info(f"Secure email sent by {user_email} with {security_level.value}")
        
        return SendEmailResponse(
            message_id=result["id"],
            thread_id=result.get("threadId"),
            security_level=security_level.value,
            encryption_applied=security_level != SecurityLevel.LEVEL_4,
            success=True,
            message="Email sent successfully"
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        await security_auditor.log_incident(
            SecurityIncidentType.SYSTEM_ERROR,
            f"Email send error: {str(e)}",
            user_id=session_payload.get("user_email") if 'session_payload' in locals() else None,
            details={"error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send email"
        )

@router.post("/messages/{message_id}/modify")
async def modify_message(
    message_id: str,
    request: MessageActionRequest,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Modify message labels or status"""
    try:
        # Validate session
        session_payload = oauth_service.validate_session_token(request.session_token)
        if not session_payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session"
            )
        
        user_email = session_payload["user_email"]
        
        # Modify message
        result = await gmail_client.modify_message(
            user_email=user_email,
            message_id=message_id,
            add_label_ids=request.add_label_ids,
            remove_label_ids=request.remove_label_ids,
            session=db
        )
        
        return {"success": True, "message": "Message modified successfully", "result": result}
    
    except GmailError as e:
        logger.error(f"Gmail API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except Exception as e:
        logger.error(f"Error modifying message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to modify message"
        )

@router.get("/labels")
async def get_labels(
    session_token: str = Query(..., description="Session token"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get user's Gmail labels"""
    try:
        # Validate session
        session_payload = oauth_service.validate_session_token(session_token)
        if not session_payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session"
            )
        
        user_email = session_payload["user_email"]
        
        # Get labels
        labels = await gmail_client.get_labels(user_email, db)
        
        return {"labels": labels}
    
    except GmailError as e:
        logger.error(f"Gmail API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except Exception as e:
        logger.error(f"Error fetching labels: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch labels"
        )

@router.get("/user/info", response_model=UserInfoResponse)
async def get_user_info(
    session_token: str = Query(..., description="Session token"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get current user information"""
    try:
        # Validate session
        session_payload = oauth_service.validate_session_token(session_token)
        if not session_payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session"
            )
        
        user_email = session_payload["user_email"]
        user_id = session_payload["user_id"]
        
        # Get user from database
        from sqlalchemy import select
        from ..models.user import User
        
        result = await db.execute(select(User).where(User.email == user_email))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserInfoResponse(
            user_id=user.id,
            email=user.email,
            display_name=user.display_name,
            last_login=user.last_login.isoformat() if user.last_login else None,
            created_at=user.created_at.isoformat(),
            oauth_connected=user.oauth_access_token is not None,
            token_expires_at=user.oauth_token_expiry.isoformat() if user.oauth_token_expiry else None
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error getting user info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information"
        )
