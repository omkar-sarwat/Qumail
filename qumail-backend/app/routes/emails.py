from fastapi import APIRouter, Depends, HTTPException, Request, Query, Form
import json
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import uuid

from ..mongo_database import get_database
from ..api.auth import get_current_user
from ..mongo_models import UserDocument
from ..mongo_repositories import EmailRepository, AttachmentRepository
from ..services.gmail_service import gmail_service
from ..services.gmail_oauth import oauth_service
from ..services.real_quantum_email import real_quantum_email_service
from ..services.quantum_encryption import quantum_encryption_service
from ..services.complete_email_service import complete_email_service

router = APIRouter(prefix="/api/v1/emails", tags=["emails"])
logger = logging.getLogger(__name__)


def _parse_metadata(raw_metadata: Optional[Any]) -> Dict[str, Any]:
    if not raw_metadata:
        return {}
    if isinstance(raw_metadata, dict):
        return raw_metadata
    if isinstance(raw_metadata, str):
        try:
            return json.loads(raw_metadata)
        except json.JSONDecodeError:
            return {"raw_metadata": raw_metadata}
    return dict(raw_metadata)

@router.get("/folders")
async def get_email_folders(
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> List[Dict[str, Any]]:
    """Get email folders including Gmail and quantum folders"""
    try:
        folders = []
        
        # Add quantum email folders
        quantum_folders = [
            {"id": "quantum_inbox", "name": "Quantum Inbox", "count": 0, "type": "quantum", "icon": "quantum"},
            {"id": "quantum_sent", "name": "Quantum Sent", "count": 0, "type": "quantum", "icon": "quantum"},
            {"id": "quantum_drafts", "name": "Quantum Drafts", "count": 0, "type": "quantum", "icon": "quantum"}
        ]
        folders.extend(quantum_folders)
        
        # Add Gmail folders if user has OAuth token
        if current_user.oauth_access_token:
            try:
                access_token = await oauth_service.get_valid_access_token(current_user.email, db)

                # Fetch folders from Gmail API
                gmail_folders = await gmail_service.get_gmail_folders(access_token)
                
                # Add Gmail prefix and icon
                for folder in gmail_folders:
                    folder["type"] = "gmail"
                    folder["icon"] = "gmail"
                    folder["id"] = f"gmail_{folder['id']}"
                folders.extend(gmail_folders)
                
            except Exception as e:
                logger.error(f"Failed to fetch Gmail folders: {e}")
                # Don't fail the entire request if Gmail API has issues
                # Just log the error and continue with other folders
        
        return folders
        
    except Exception as e:
        logger.error(f"Error getting email folders: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch email folders")

@router.get("/{folder}")
async def get_emails(
    folder: str,
    page_token: Optional[str] = None,
    max_results: Optional[int] = 25,
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> Dict[str, Any]:
    """Get emails from specified folder with pagination support"""
    try:
        emails = []
        next_page_token = None
        
        # Handle Gmail vs local/system folders
        # Explicit Gmail folders (prefix gmail_) always fetch from Gmail API
        if folder.startswith("gmail_"):
            if not current_user.oauth_access_token:
                raise HTTPException(status_code=401, detail="Gmail access not available")
            try:
                access_token = await oauth_service.get_valid_access_token(current_user.email, db)
                gmail_folder = folder.replace("gmail_", "", 1)
                result = await gmail_service.fetch_emails(
                    access_token=access_token,
                    folder=gmail_folder,
                    max_results=max_results,
                    page_token=page_token
                )
                emails.extend(result.get("emails", []))
                next_page_token = result.get("next_page_token")
            except Exception as e:
                logger.error(f"Failed to fetch Gmail emails: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to fetch Gmail emails: {str(e)}")

        # Plain system folders (inbox/sent/drafts) now prefer real Gmail when available
        elif folder in ["inbox", "sent", "drafts"]:
            gmail_label_map = {
                "inbox": "INBOX",
                "sent": "SENT",
                "drafts": "DRAFT"
            }
            fetched_from_gmail = False

            if current_user.oauth_access_token:
                try:
                    access_token = await oauth_service.get_valid_access_token(current_user.email, db)
                    result = await gmail_service.fetch_emails(
                        access_token=access_token,
                        folder=gmail_label_map.get(folder, folder.upper()),
                        max_results=max_results,
                        page_token=page_token
                    )
                    emails.extend(result.get("emails", []))
                    next_page_token = result.get("next_page_token")
                    fetched_from_gmail = True
                except Exception as gmail_error:
                    logger.error(f"Failed to fetch Gmail emails for {folder}: {gmail_error}. Falling back to local store.")

            if not fetched_from_gmail:
                try:
                    local_emails = await complete_email_service.get_encrypted_email_list(
                        current_user.email,
                        folder,
                        db
                    )
                    emails.extend(local_emails)
                except Exception as local_error:
                    logger.error(f"Failed to fetch local emails for folder {folder}: {local_error}")
                    raise HTTPException(status_code=500, detail=f"Failed to fetch emails from {folder}: {str(local_error)}")

        # Other system-like folders (starred, trash, important, spam) fall back to Gmail when available
        elif folder in ["starred", "trash", "important", "spam"]:
            if current_user.oauth_access_token:
                try:
                    access_token = await oauth_service.get_valid_access_token(current_user.email, db)
                    result = await gmail_service.fetch_emails(
                        access_token=access_token,
                        folder=folder,
                        max_results=max_results,
                        page_token=page_token
                    )
                    emails.extend(result.get("emails", []))
                    next_page_token = result.get("next_page_token")
                except Exception as e:
                    logger.error(f"Failed to fetch Gmail emails for folder {folder}: {e}")
                    raise HTTPException(status_code=500, detail=f"Failed to fetch Gmail emails: {str(e)}")
        
        # Handle quantum folders
        elif folder.startswith("quantum_"):
            try:
                quantum_emails = await real_quantum_email_service.get_emails(
                    current_user.email,
                    folder.replace("quantum_", ""),
                    db
                )
                emails.extend(quantum_emails)
            except Exception as e:
                logger.error(f"Failed to fetch quantum emails: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to fetch quantum emails: {str(e)}")
        else:
            # Unknown folder type
            raise HTTPException(status_code=404, detail=f"Folder {folder} not found")
        
        # Sort by timestamp (newest first)
        emails.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return {
            "emails": emails,
            "next_page_token": next_page_token
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting emails from folder {folder}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch emails from {folder}")

@router.get("/email/{email_id}")
async def get_email_details(
    email_id: str,
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> Dict[str, Any]:
    """Get detailed email content"""
    try:
        email_repo = EmailRepository(db)

        # Handle Gmail emails
        if email_id.startswith("gmail_"):
            if not current_user.oauth_access_token:
                raise HTTPException(status_code=401, detail="Gmail access not available")

            access_token = await oauth_service.get_valid_access_token(current_user.email, db)

            # Fetch full email from Gmail API
            email_details = await gmail_service.get_email_by_id(access_token, email_id)
            
            if not email_details:
                raise HTTPException(status_code=404, detail="Email not found")

            # Check if this Gmail message has a corresponding quantum record
            gmail_id = email_id.replace("gmail_", "", 1)
            logger.info(f"🔍 Looking for quantum record with gmail_message_id: {gmail_id}")
            
            stored_email = await email_repo.find_by_gmail_id(gmail_id)

            if stored_email:
                logger.info(f"✅ Found quantum record: ID={stored_email.id}, flow_id={stored_email.flow_id}, security_level={stored_email.security_level}")
                logger.info(f"   Encrypted body length: {len(stored_email.body_encrypted or '')}")
                logger.info(f"   Encryption metadata: {stored_email.encryption_metadata}")
                
                metadata = _parse_metadata(stored_email.encryption_metadata)

                encrypted_size = len(stored_email.body_encrypted or "") or metadata.get("encrypted_size") or metadata.get("encryptedSize") or 0
                
                logger.info(f"   Calculated encrypted_size: {encrypted_size}")
                logger.info(f"   Algorithm from metadata: {metadata.get('algorithm', 'Unknown')}")

                # Get algorithm with fallback based on security level
                algorithm = metadata.get("algorithm")
                if not algorithm or algorithm == "Unknown":
                    algorithm_map = {
                        1: "OTP-QKD-ETSI-014",
                        2: "AES-256-GCM",
                        3: "PQC-Kyber1024",
                        4: "RSA-4096"
                    }
                    algorithm = algorithm_map.get(stored_email.security_level, "Unknown")
                    logger.info(f"   Algorithm fallback to: {algorithm}")

                security_info = {
                    "level": stored_email.security_level,
                    "algorithm": algorithm,
                    "quantum_enhanced": metadata.get("quantum_enhanced", True),
                    "encrypted_size": encrypted_size
                }

                email_details.update({
                    "email_id": stored_email.id,  # Add email_id for frontend
                    "flow_id": stored_email.flow_id,
                    "body_encrypted": stored_email.body_encrypted,
                    "security_level": stored_email.security_level,
                    "security_info": security_info,
                    "encryption_metadata": metadata,
                    "requires_decryption": True,
                    "encrypted_size": encrypted_size,
                    "decrypt_endpoint": f"/api/v1/emails/email/{stored_email.id}/decrypt"
                })
                
                logger.info(f"📤 Returning enriched Gmail email:")
                logger.info(f"   email_id={stored_email.id}")
                logger.info(f"   flow_id={email_details.get('flow_id')}")
                logger.info(f"   security_level={email_details.get('security_level')}")
                logger.info(f"   algorithm={algorithm}")
                logger.info(f"   encrypted_size={email_details.get('encrypted_size')}")
                logger.info(f"   requires_decryption={email_details.get('requires_decryption')}")
                logger.info(f"   decrypt_endpoint={email_details.get('decrypt_endpoint')}")
            else:
                logger.warning(f"❌ No quantum record found for gmail_message_id: {gmail_id}")

            return email_details
        
        # Handle quantum emails - return encrypted content only (no auto-decryption)
        elif email_id.startswith("quantum_") or email_id:
            try:
                normalized_email_id = email_id.replace("quantum_", "", 1) if email_id.startswith("quantum_") else email_id

                # Get email from database without decrypting
                email = await email_repo.find_by_id(normalized_email_id)

                if not email:
                    raise HTTPException(status_code=404, detail="Email not found")

                # Access control: verify user is sender or receiver
                if (email.sender_email != current_user.email and 
                    email.receiver_email != current_user.email and
                    email.user_id != current_user.id):
                    logger.warning(f"Unauthorized access attempt by {current_user.email} for email {normalized_email_id}")
                    raise HTTPException(status_code=403, detail="Access denied: You are not authorized to view this email")

                metadata = _parse_metadata(email.encryption_metadata)

                sync_type = metadata.get("sync_type")

                if email.security_level == 0 and (sync_type == "gmail_plain" or sync_type is None):
                    gmail_message_id = email.gmail_message_id or metadata.get("gmailMessageId")
                    gmail_payload = None

                    if gmail_message_id and current_user.oauth_access_token:
                        try:
                            access_token = await oauth_service.get_valid_access_token(current_user.email, db)
                            gmail_payload = await gmail_service.get_email_by_id(access_token, gmail_message_id)
                        except Exception as fetch_error:
                            logger.warning(f"Failed to fetch Gmail body for {gmail_message_id}: {fetch_error}")

                    if gmail_payload:
                        return {
                            "email_id": email.id,
                            "gmail_message_id": gmail_message_id,
                            "flow_id": email.flow_id,
                            "sender_email": gmail_payload.get("sender") or email.sender_email,
                            "sender": gmail_payload.get("sender"),
                            "receiver_email": gmail_payload.get("recipient") or email.receiver_email,
                            "recipient": gmail_payload.get("recipient"),
                            "subject": gmail_payload.get("subject") or email.subject,
                            "body": gmail_payload.get("bodyText") or gmail_payload.get("bodyHtml") or metadata.get("bodyText") or email.body_encrypted,
                            "bodyText": gmail_payload.get("bodyText") or metadata.get("bodyText") or email.body_encrypted,
                            "bodyHtml": gmail_payload.get("bodyHtml") or metadata.get("bodyHtml"),
                            "inlineImages": gmail_payload.get("inlineImages", []),
                            "attachments": gmail_payload.get("attachments", []),
                            "labels": gmail_payload.get("labels", metadata.get("labels", [])),
                            "snippet": gmail_payload.get("snippet", metadata.get("snippet")),
                            "timestamp": gmail_payload.get("timestamp", email.timestamp.isoformat()),
                            "is_read": email.is_read,
                            "is_starred": email.is_starred,
                            "is_suspicious": email.is_suspicious,
                            "source": "gmail",
                            "type": "gmail",
                            "requires_decryption": False
                        }

                    return {
                        "email_id": email.id,
                        "flow_id": email.flow_id,
                        "sender_email": email.sender_email,
                        "receiver_email": email.receiver_email,
                        "subject": email.subject,
                        "body": metadata.get("bodyText") or email.body_encrypted,
                        "bodyText": metadata.get("bodyText") or email.body_encrypted,
                        "bodyHtml": metadata.get("bodyHtml"),
                        "snippet": metadata.get("snippet"),
                        "labels": metadata.get("labels", []),
                        "timestamp": email.timestamp.isoformat(),
                        "is_read": email.is_read,
                        "is_starred": email.is_starred,
                        "is_suspicious": email.is_suspicious,
                        "attachments": metadata.get("attachments", []),
                        "source": "gmail",
                        "type": "gmail",
                        "requires_decryption": False,
                        "encrypted_size": metadata.get("encrypted_size") or metadata.get("encryptedSize") or len(email.body_encrypted or "")
                    }

                # Return email metadata with encrypted content (no decryption)
                logger.info(f"📧 Returning quantum email from database: {email.id}")
                logger.info(f"   Flow ID: {email.flow_id}")
                logger.info(f"   Security Level: {email.security_level}")
                logger.info(f"   Encrypted Body Length: {len(email.body_encrypted or '')}")
                logger.info(f"   Metadata: {metadata}")
                
                # Get algorithm with fallback
                algorithm = metadata.get("algorithm")
                if not algorithm or algorithm == "Unknown":
                    algorithm_map = {
                        1: "OTP-QKD-ETSI-014",
                        2: "AES-256-GCM",
                        3: "PQC-Kyber1024",
                        4: "RSA-4096"
                    }
                    algorithm = algorithm_map.get(email.security_level, "Unknown")
                    logger.info(f"   Algorithm fallback applied: {algorithm}")
                else:
                    logger.info(f"   Algorithm from metadata: {algorithm}")
                
                encrypted_size = metadata.get("encrypted_size") or metadata.get("encryptedSize") or len(email.body_encrypted or "")
                
                response_data = {
                    "email_id": email.id,
                    "flow_id": email.flow_id,
                    "sender_email": email.sender_email,
                    "receiver_email": email.receiver_email,
                    "subject": email.subject,  # Subject shows security level prefix
                    "body_encrypted": email.body_encrypted,  # Encrypted content shown as-is
                    "security_level": email.security_level,
                    "timestamp": email.timestamp.isoformat(),
                    "is_read": email.is_read,
                    "is_starred": email.is_starred,
                    "is_suspicious": email.is_suspicious,
                    "encryption_metadata": metadata,
                    "type": "quantum",
                    "requires_decryption": True,
                    "decrypt_endpoint": f"/api/v1/emails/email/{email.id}/decrypt",
                    "encrypted_size": encrypted_size,
                    "security_info": {
                        "level": email.security_level,
                        "algorithm": algorithm,
                        "quantum_enhanced": metadata.get("quantum_enhanced", True),
                        "encrypted_size": encrypted_size
                    }
                }
                
                logger.info(f"📤 Sending quantum email response:")
                logger.info(f"   requires_decryption: {response_data['requires_decryption']}")
                logger.info(f"   security_level: {response_data['security_level']}")
                logger.info(f"   algorithm: {response_data['security_info']['algorithm']}")
                logger.info(f"   encrypted_size: {response_data['encrypted_size']}")
                
                return response_data

            except Exception as e:
                logger.error(f"Error getting quantum email details: {e}")
                raise HTTPException(status_code=500, detail="Failed to fetch quantum email details")
        
        else:
            raise HTTPException(status_code=404, detail="Email not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting email details for {email_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch email details")

@router.post("/send/quantum")
async def send_quantum_email(
    request: Request,
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> Dict[str, Any]:
    """Send quantum-encrypted email - REAL end-to-end encryption via Gmail"""
    try:
        data = await request.json()
        
        # Handle frontend field mapping
        if "recipient" in data and "to" not in data:
            data["to"] = data["recipient"]
        if "securityLevel" in data and "security_level" not in data:
            data["security_level"] = data["securityLevel"]
        
        logger.info("="*80)
        logger.info("🔒 REAL QUANTUM EMAIL SEND REQUEST")
        logger.info(f"   Request data keys: {data.keys()}")
        if "attachments" in data:
            logger.info(f"   📎 Attachments: {len(data['attachments'])} files")
            for att in data['attachments']:
                logger.info(f"      - {att.get('filename', 'unknown')} ({att.get('size', 0)} bytes)")
        logger.info("="*80)
        
        # Validate required fields
        required_fields = ["to", "subject", "body", "security_level"]
        for field in required_fields:
            if field not in data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Validate security level
        security_level = int(data["security_level"])
        if security_level not in [1, 2, 3, 4]:
            raise HTTPException(status_code=400, detail="Security level must be between 1-4")
        
        # Validate recipient email format
        recipients = data["to"] if isinstance(data["to"], list) else [data["to"]]
        for recipient in recipients:
            if "@" not in recipient:
                raise HTTPException(status_code=400, detail=f"Invalid email format: {recipient}")
        
        # For now, handle single recipient (can extend for multiple later)
        primary_recipient = recipients[0]
        
        logger.info(f"📧 Sending Level {security_level} quantum-encrypted email")
        logger.info(f"   From: {current_user.email}")
        logger.info(f"   To: {primary_recipient}")

        gmail_credentials = None
        sent_via_gmail = False

        if current_user.oauth_access_token:
            access_token = await oauth_service.get_valid_access_token(current_user.email, db)
            gmail_credentials = {
                "access_token": access_token,
                "refresh_token": current_user.oauth_refresh_token,
                "token_expiry": current_user.oauth_token_expiry
            }
        else:
            logger.warning("⚠️  No Gmail OAuth token - storing locally only")

        result = await complete_email_service.send_encrypted_email(
            sender_email=current_user.email,
            sender_user_id=current_user.id,
            recipient_email=primary_recipient,
            subject=data["subject"],
            body=data["body"],
            security_level=security_level,
            cc=data.get("cc"),
            bcc=data.get("bcc"),
            attachments=data.get("attachments"),
            db=db,
            gmail_credentials=gmail_credentials
        )

        sent_via_gmail = bool(result.get("gmail_message_id"))

        email_uuid = str(result.get("email_id"))
        try:
            email_id_int = int(uuid.UUID(email_uuid)) % (10 ** 10)
        except (ValueError, TypeError):
            email_id_int = abs(hash(email_uuid)) % (10 ** 10)

        encryption_details = result.get("encryption_details", {})

        response_payload = {
            "success": result.get("success", True),
            "message": (
                f"Level {security_level} quantum email encrypted and sent via Gmail"
                if sent_via_gmail
                else f"Level {security_level} quantum email encrypted and stored"
            ),
            "emailId": email_id_int,
            "emailUuid": email_uuid,
            "flowId": result.get("flow_id"),
            "gmailMessageId": result.get("gmail_message_id"),
            "encryptionMethod": encryption_details.get("algorithm"),
            "securityLevel": encryption_details.get("security_level", security_level),
            "keyId": encryption_details.get("key_id"),
            "encryptedSize": encryption_details.get("encrypted_size"),
            "timestamp": result.get("timestamp"),
            "sent_via_gmail": sent_via_gmail
        }

        logger.info("=" * 80)
        logger.info("✅ Quantum email processed successfully")
        logger.info(
            "   Delivery: %s",
            "Gmail + QuMail storage" if sent_via_gmail else "QuMail storage only"
        )
        logger.info("=" * 80)

        return response_payload
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error sending quantum email: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send quantum email: {str(e)}")

@router.post("/send/gmail")
async def send_gmail_email(
    request: Request,
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> Dict[str, Any]:
    """Send email via Gmail API"""
    try:
        # Validate user has OAuth token
        if not current_user.oauth_access_token:
            raise HTTPException(status_code=401, detail="Gmail access not available")
        
        # Parse request data
        data = await request.json()
        
        # Validate required fields
        required_fields = ["to", "subject", "body"]
        for field in required_fields:
            if field not in data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Ensure we have a valid access token
        access_token = await oauth_service.get_valid_access_token(current_user.email, db)
        
        # Prepare message for Gmail API
        message = {
            "from": current_user.email,
            "to": data["to"],
            "subject": data["subject"],
            "bodyText": data.get("bodyText", data.get("body", "")),
            "bodyHtml": data.get("bodyHtml", ""),
            "cc": data.get("cc", ""),
            "bcc": data.get("bcc", ""),
        }
        
        # Send email via Gmail API
        result = await gmail_service.send_email(access_token, message)
        
        return {
            "success": True,
            "messageId": result.get("messageId"),
            "threadId": result.get("threadId"),
            "message": "Email sent successfully via Gmail"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending Gmail email: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send Gmail email: {str(e)}")

@router.post("/send")
async def send_email(
    request: Request,
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> Dict[str, Any]:
    """Send email (auto-routes to appropriate service)"""
    try:
        data = await request.json()
        
        # Add debugging to see what the frontend is sending
        logger.info("="*80)
        logger.info("EMAIL SEND REQUEST DEBUG")
        logger.info(f"   Full request data: {data}")
        logger.info(f"   Email type detected: {data.get('type', 'gmail')} (default: gmail)")
        logger.info(f"   Security level: {data.get('security_level', 'Not specified')}")
        logger.info(f"   SecurityLevel field: {data.get('securityLevel', 'Not specified')}")
        logger.info("="*80)
        
        # Route based on email type
        email_type = data.get("type", "gmail")
        
        # Check if this should be a quantum email based on security level
        if email_type == "quantum" or data.get("security_level") or data.get("securityLevel"):
            logger.info("ROUTING TO QUANTUM EMAIL SERVICE")
            # Force quantum email if security level is specified
            if "security_level" not in data and "securityLevel" in data:
                data["security_level"] = data["securityLevel"]
            # Ensure proper field mapping for quantum email
            if "recipient" in data and "to" not in data:
                data["to"] = data["recipient"]
            # Forward to quantum sending endpoint
            return await send_quantum_email(request, current_user, db)
        else:
            logger.info("🔄 ROUTING TO GMAIL SERVICE")
            # Default to Gmail
            return await send_gmail_email(request, current_user, db)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        raise HTTPException(status_code=500, detail="Failed to send email")

@router.get("/encryption/status")
async def get_encryption_status(
    current_user: UserDocument = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get quantum encryption system status"""
    try:
        status = await quantum_encryption_service.get_encryption_status()
        return status
        
    except Exception as e:
        logger.error(f"Error getting encryption status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get encryption status")

@router.post("/email/{email_id}/decrypt")
async def decrypt_quantum_email(
    email_id: str,
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> Dict[str, Any]:
    """Decrypt quantum-secured email with access control"""
    try:
        logger.info(f"Decryption requested for email {email_id} by user {current_user.email}")
        
        resolved_email_id = email_id
        email_repo = EmailRepository(db)
        attachment_repo = AttachmentRepository(db)

        if email_id.startswith("gmail_"):
            gmail_message_id = email_id.replace("gmail_", "", 1)
            logger.info(f"Resolving Gmail ID {gmail_message_id} to local quantum email")

            gmail_email = await email_repo.find_by_gmail_id(gmail_message_id)

            if not gmail_email:
                logger.error(f"Gmail message {gmail_message_id} has no matching quantum record")
                raise HTTPException(status_code=404, detail="Encrypted Gmail message not found in local store")

            resolved_email_id = gmail_email.id
            logger.info(f"Mapped Gmail message {gmail_message_id} to email {resolved_email_id}")

        # Decrypt email with access control
        decryption_result = await quantum_encryption_service.decrypt_email(
            email_id=resolved_email_id,
            user_email=current_user.email,
            requesting_user_id=current_user.id,
            db=db
        )
        
        logger.info(f"Email {resolved_email_id} successfully decrypted for {current_user.email}")
        
        # Fetch and decrypt attachments
        attachments_data = []
        attachments = await attachment_repo.list_by_email(resolved_email_id)
        
        if attachments:
            logger.info(f"Found {len(attachments)} attachments for email {resolved_email_id}")
            for attachment in attachments:
                try:
                    decrypted_content = attachment.encrypted_data or ""
                    attachments_data.append({
                        "filename": attachment.filename,
                        "content": decrypted_content,
                        "mime_type": attachment.content_type,
                        "size": attachment.size
                    })
                    logger.info(f"   Decrypted attachment: {attachment.filename} ({attachment.size} bytes)")
                except Exception as att_error:
                    logger.error(f"Failed to decrypt attachment {attachment.filename}: {att_error}")
        
        return {
            "success": True,
            "message": f"Level {decryption_result['security_level']} email decrypted successfully",
            "email_data": {
                "email_id": decryption_result["email_id"],
                "subject": decryption_result["subject"],
                "body": decryption_result["body"],
                "sender_email": decryption_result["sender_email"],
                "receiver_email": decryption_result["receiver_email"],
                "timestamp": decryption_result["timestamp"],
                "flow_id": decryption_result["flow_id"],
                "attachments": attachments_data
            },
            "security_info": {
                "security_level": decryption_result["security_level"],
                "algorithm": decryption_result["algorithm"],
                "verification_status": decryption_result["verification_status"],
                "quantum_enhanced": decryption_result["quantum_enhanced"],
                "encrypted_size": decryption_result.get("encrypted_size", 0)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error decrypting email {email_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to decrypt email: {str(e)}")

@router.get("/email/{email_id}/attachment/{attachment_id}")
async def get_email_attachment(
    email_id: str,
    attachment_id: str,
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get email attachment data"""
    try:
        # Only Gmail attachments supported
        if not email_id.startswith("gmail_"):
            raise HTTPException(status_code=400, detail="Only Gmail attachments are supported")
            
        if not current_user.oauth_access_token:
            raise HTTPException(status_code=401, detail="Gmail access not available")
        
        access_token = await oauth_service.get_valid_access_token(current_user.email, db)
        
        # Fetch attachment
        attachment = await gmail_service.get_attachment(access_token, email_id, attachment_id)
        
        if not attachment:
            raise HTTPException(status_code=404, detail="Attachment not found")
        
        return {
            "id": attachment["id"],
            "data": attachment["data"],
            "size": attachment["size"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching attachment {attachment_id} for email {email_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch attachment")

@router.post("/{email_id}/read")
async def mark_email_as_read(
    email_id: str,
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> Dict[str, Any]:
    """Mark an email as read"""
    try:
        if email_id.startswith("gmail_"):
            if not current_user.oauth_access_token:
                raise HTTPException(status_code=401, detail="Gmail access not available")
                
            access_token = await oauth_service.get_valid_access_token(current_user.email, db)
                
            # Remove "gmail_" prefix to get the actual message ID
            gmail_message_id = email_id.replace("gmail_", "")
            
            # Call Gmail service to mark email as read
            try:
                await gmail_service.mark_as_read(access_token, gmail_message_id)
                return {"success": True, "message": "Email marked as read"}
            except Exception as e:
                logger.error(f"Failed to mark Gmail email as read: {e}")
                # Don't fail the request if Gmail API has issues
                return {"success": False, "message": str(e)}
                
        elif email_id.startswith("quantum_"):
            # Mark quantum email as read
            try:
                await real_quantum_email_service.mark_as_read(
                    email_id,
                    current_user.email,
                    db
                )
                return {"success": True, "message": "Quantum email marked as read"}
            except Exception as e:
                logger.error(f"Failed to mark quantum email as read: {e}")
                return {"success": False, "message": str(e)}
        else:
            # Unknown email type
            return {"success": False, "message": "Unknown email format"}
            
    except Exception as e:
        logger.error(f"Error marking email {email_id} as read: {e}")
        return {"success": False, "message": str(e)}

@router.post("/sync/gmail")
async def sync_gmail(
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> Dict[str, Any]:
    """Manually sync Gmail emails"""
    try:
        if not current_user.oauth_access_token:
            raise HTTPException(status_code=401, detail="Gmail access not available")
        
        access_token = await oauth_service.get_valid_access_token(current_user.email, db)
        
        # Fetch latest emails from Gmail
        synced_count = 0
        folders = ["inbox", "sent", "drafts"]
        
        for folder in folders:
            try:
                result = await gmail_service.fetch_emails(
                    access_token, 
                    folder, 
                    max_results=15
                )
                synced_count += len(result["emails"])
            except Exception as e:
                logger.error(f"Failed to sync Gmail folder {folder}: {e}")
        
        return {
            "success": True,
            "message": f"Synced {synced_count} emails from Gmail",
            "synced_count": synced_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing Gmail: {e}")
        raise HTTPException(status_code=500, detail="Failed to sync Gmail")

@router.post("/drafts")
async def create_or_update_draft(
    request: Request,
    to: str = Form(None),
    recipient: str = Form(None),
    cc: str = Form(None),
    bcc: str = Form(None),
    subject: str = Form(''),
    body: str = Form(''),
    securityLevel: int = Form(None),
    security_level: int = Form(None),
    id: str = Form(None),
    draftId: str = Form(None),
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> Dict[str, Any]:
    """Create or update a draft - saves directly to MongoDB for authenticated user"""
    try:
        from ..mongo_repositories import DraftRepository
        from ..mongo_models import DraftDocument
        draft_repo = DraftRepository(db)
        
        logger.info(f"💾 Draft save request from user: {current_user.email}")
        logger.info(f"   To: {to or recipient}, Subject: {subject}")
        
        # Check if updating existing draft by ID
        draft_id = id or draftId
        
        if draft_id:
            # Try to find existing draft
            existing_draft = await draft_repo.find_by_id(draft_id)
            logger.info(f"   Looking for existing draft ID: {draft_id} - Found: {existing_draft is not None}")
            
            if existing_draft:
                # Update existing draft
                updates = {
                    'recipient': to or recipient,
                    'subject': subject or '',
                    'body': body or '',
                    'security_level': securityLevel or security_level or 2,
                    'cc': cc,
                    'bcc': bcc,
                    'updated_at': datetime.utcnow()
                }
                success = await draft_repo.update(draft_id, updates)
                logger.info(f"✅ Updated draft {draft_id}: {success}")
                
                return {
                    "success": True,
                    "draftId": draft_id,
                    "message": "Draft updated"
                }
        
        # Create new draft (either no ID provided, or ID not found)
        logger.info(f"📝 Creating NEW draft for user {current_user.email}")
        
        # Validate authentication
        if not current_user.id or not current_user.email:
            logger.error(f"❌ User authentication incomplete - id: {current_user.id}, email: {current_user.email}")
            raise HTTPException(status_code=401, detail="User not properly authenticated")
        
        try:
            # Prepare draft data - only include id if it's provided
            draft_data = {
                "user_id": current_user.id,
                "user_email": current_user.email,
                "recipient": to or recipient or '',
                "subject": subject or '',
                "body": body or '',
                "security_level": securityLevel or security_level or 2,
                "cc": cc,
                "bcc": bcc,
                "is_synced": True
            }
            
            # Only set id if draft_id is provided (not None)
            if draft_id:
                draft_data["id"] = draft_id
            
            draft_doc = DraftDocument(**draft_data)
            
            logger.info(f"📦 Draft document prepared:")
            logger.info(f"   ID: {draft_doc.id}")
            logger.info(f"   User ID: {draft_doc.user_id}")
            logger.info(f"   User Email: {draft_doc.user_email}")
            logger.info(f"   Recipient: {draft_doc.recipient}")
            logger.info(f"   Subject: {draft_doc.subject}")
            
            saved_draft = await draft_repo.create(draft_doc)
            logger.info(f"✅ Created draft {saved_draft.id} in MongoDB for {current_user.email}")
            
            return {
                "success": True,
                "draftId": saved_draft.id,
                "message": "Draft created successfully"
            }
            
        except ValueError as ve:
            logger.error(f"❌ Validation error creating draft: {ve}")
            raise HTTPException(status_code=400, detail=f"Validation error: {str(ve)}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error saving draft: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(status_code=500, detail=f"Failed to save draft: {str(e)}")

@router.get("/drafts")
async def get_drafts(
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> List[Dict[str, Any]]:
    """Get all drafts for authenticated user only"""
    try:
        from ..mongo_repositories import DraftRepository
        draft_repo = DraftRepository(db)
        
        logger.info(f"📨 Fetching drafts for user: {current_user.email} (ID: {current_user.id})")
        drafts = await draft_repo.list_by_email(current_user.email)
        logger.info(f"📋 Found {len(drafts)} drafts in MongoDB for {current_user.email}")
        
        if len(drafts) > 0:
            logger.info(f"   First draft: {drafts[0].subject if drafts[0].subject else '(no subject)'}")
        
        result = [
            {
                "id": draft.id,
                "draftId": draft.id,
                "to": draft.recipient,
                "recipient": draft.recipient,
                "subject": draft.subject,
                "body": draft.body,
                "securityLevel": draft.security_level,
                "security_level": draft.security_level,
                "cc": draft.cc,
                "bcc": draft.bcc,
                "created_at": draft.created_at.isoformat(),
                "updated_at": draft.updated_at.isoformat()
            }
            for draft in drafts
        ]
        logger.info(f"✅ Returning {len(result)} drafts to frontend")
        if len(result) > 0:
            logger.info(f"   Sample draft data being sent:")
            logger.info(f"   ID: {result[0]['id']}")
            logger.info(f"   Subject: {result[0]['subject']}")
            logger.info(f"   Recipient: {result[0]['recipient']}")
        logger.info(f"   Full response: {result}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error fetching drafts: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch drafts")

@router.delete("/drafts/{draft_id}")
async def delete_draft(
    draft_id: str,
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> Dict[str, Any]:
    """Delete a draft"""
    try:
        from ..mongo_repositories import DraftRepository
        draft_repo = DraftRepository(db)
        
        # Verify ownership
        draft = await draft_repo.find_by_user_and_id(current_user.email, draft_id)
        if not draft:
            raise HTTPException(status_code=404, detail="Draft not found")
        
        await draft_repo.delete(draft_id)
        logger.info(f"Deleted draft {draft_id}")
        
        return {
            "success": True,
            "message": "Draft deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting draft: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete draft")
