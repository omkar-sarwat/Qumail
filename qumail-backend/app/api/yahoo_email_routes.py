"""
Yahoo Email Routes - Email operations via Yahoo Mail API
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel, EmailStr
import logging

from ..mongo_models import UserDocument
from ..api.auth import get_current_user
from ..services.yahoo_mail_service import yahoo_mail_service
from ..services.yahoo_oauth import yahoo_oauth_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/yahoo/mail", tags=["Yahoo Mail"])


class SendEmailRequest(BaseModel):
    """Request model for sending email"""
    to: List[EmailStr]
    subject: str
    body: str
    cc: Optional[List[EmailStr]] = None
    bcc: Optional[List[EmailStr]] = None
    is_html: bool = True


class DraftRequest(BaseModel):
    """Request model for creating draft"""
    to: List[EmailStr]
    subject: str
    body: str
    cc: Optional[List[EmailStr]] = None
    bcc: Optional[List[EmailStr]] = None
    is_html: bool = True


async def get_yahoo_token(user: UserDocument) -> str:
    """Get valid Yahoo access token for user"""
    # Check if user has Yahoo tokens
    if not user.yahoo_tokens:
        raise HTTPException(
            status_code=401,
            detail="Yahoo account not connected. Please connect your Yahoo account first."
        )
    
    # Check if token needs refresh
    access_token = await yahoo_oauth_service.get_valid_token(user.id)
    
    if not access_token:
        raise HTTPException(
            status_code=401,
            detail="Yahoo token expired. Please reconnect your Yahoo account."
        )
    
    return access_token


@router.get("/folders")
async def get_folders(
    current_user: UserDocument = Depends(get_current_user)
):
    """Get list of Yahoo Mail folders"""
    try:
        access_token = await get_yahoo_token(current_user)
        folders = await yahoo_mail_service.get_folders(access_token)
        
        return {
            "success": True,
            "folders": folders
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get Yahoo folders: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/messages")
async def get_messages(
    folder: str = Query("Inbox", description="Folder to fetch from"),
    count: int = Query(20, ge=1, le=100, description="Number of messages"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: UserDocument = Depends(get_current_user)
):
    """Get messages from specified folder"""
    try:
        access_token = await get_yahoo_token(current_user)
        
        result = await yahoo_mail_service.get_inbox_messages(
            access_token=access_token,
            count=count,
            offset=offset,
            folder_id=folder
        )
        
        return {
            "success": True,
            **result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get Yahoo messages: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/messages/{message_id}")
async def get_message(
    message_id: str,
    current_user: UserDocument = Depends(get_current_user)
):
    """Get full message details"""
    try:
        access_token = await get_yahoo_token(current_user)
        message = await yahoo_mail_service.get_message(access_token, message_id)
        
        return {
            "success": True,
            "message": message
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get Yahoo message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send")
async def send_email(
    request: SendEmailRequest,
    current_user: UserDocument = Depends(get_current_user)
):
    """Send email via Yahoo Mail"""
    try:
        access_token = await get_yahoo_token(current_user)
        
        result = await yahoo_mail_service.send_message(
            access_token=access_token,
            to=request.to,
            subject=request.subject,
            body=request.body,
            cc=request.cc,
            bcc=request.bcc,
            is_html=request.is_html
        )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send Yahoo email: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/messages/{message_id}/read")
async def mark_as_read(
    message_id: str,
    current_user: UserDocument = Depends(get_current_user)
):
    """Mark message as read"""
    try:
        access_token = await get_yahoo_token(current_user)
        success = await yahoo_mail_service.mark_as_read(access_token, message_id)
        
        return {"success": success}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to mark message as read: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/messages/{message_id}/unread")
async def mark_as_unread(
    message_id: str,
    current_user: UserDocument = Depends(get_current_user)
):
    """Mark message as unread"""
    try:
        access_token = await get_yahoo_token(current_user)
        success = await yahoo_mail_service.mark_as_unread(access_token, message_id)
        
        return {"success": success}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to mark message as unread: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/messages/{message_id}")
async def delete_message(
    message_id: str,
    current_user: UserDocument = Depends(get_current_user)
):
    """Delete message (move to trash)"""
    try:
        access_token = await get_yahoo_token(current_user)
        success = await yahoo_mail_service.delete_message(access_token, message_id)
        
        return {"success": success}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/messages/{message_id}/move")
async def move_message(
    message_id: str,
    folder_id: str = Query(..., description="Target folder ID"),
    current_user: UserDocument = Depends(get_current_user)
):
    """Move message to specified folder"""
    try:
        access_token = await get_yahoo_token(current_user)
        success = await yahoo_mail_service.move_to_folder(access_token, message_id, folder_id)
        
        return {"success": success}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to move message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_messages(
    q: str = Query(..., description="Search query"),
    count: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: UserDocument = Depends(get_current_user)
):
    """Search messages"""
    try:
        access_token = await get_yahoo_token(current_user)
        
        result = await yahoo_mail_service.search_messages(
            access_token=access_token,
            query=q,
            count=count,
            offset=offset
        )
        
        return {
            "success": True,
            **result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to search Yahoo messages: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/drafts")
async def create_draft(
    request: DraftRequest,
    current_user: UserDocument = Depends(get_current_user)
):
    """Create a draft email"""
    try:
        access_token = await get_yahoo_token(current_user)
        
        result = await yahoo_mail_service.create_draft(
            access_token=access_token,
            to=request.to,
            subject=request.subject,
            body=request.body,
            cc=request.cc,
            bcc=request.bcc,
            is_html=request.is_html
        )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create Yahoo draft: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
