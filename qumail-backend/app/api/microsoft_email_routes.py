"""
Microsoft Graph Email Routes
API endpoints for fetching and sending emails via Microsoft Graph API
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel, EmailStr
from typing import List, Optional
import logging
from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorDatabase

from ..mongo_database import get_database
from ..services.microsoft_graph import microsoft_graph_client, GraphEmail, GraphSendResult
from ..services.microsoft_oauth import MicrosoftOAuthError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/microsoft", tags=["Microsoft Graph Email"])


class GraphEmailResponse(BaseModel):
    """Email response model"""
    id: str
    message_id: str
    thread_id: str
    subject: str
    from_address: str
    from_name: str
    to_address: str
    to_name: str
    cc_address: Optional[str]
    body_text: str
    body_html: Optional[str]
    date: str
    is_read: bool
    has_attachments: bool
    folder: str
    importance: str


class FetchEmailsResponse(BaseModel):
    """Response for fetching emails"""
    success: bool
    emails: List[GraphEmailResponse]
    count: int
    message: str


class SendEmailRequest(BaseModel):
    """Request to send email via Graph API"""
    user_email: EmailStr  # The sender's Microsoft account email
    to_address: str
    subject: str
    body_text: str
    body_html: Optional[str] = None
    cc_address: Optional[str] = None
    bcc_address: Optional[str] = None


class SendEmailResponse(BaseModel):
    """Response for sending email"""
    success: bool
    message_id: Optional[str]
    message: str


class MarkReadRequest(BaseModel):
    """Request to mark email as read/unread"""
    user_email: EmailStr
    message_id: str
    is_read: bool = True


class DeleteEmailRequest(BaseModel):
    """Request to delete email"""
    user_email: EmailStr
    message_id: str


def _graph_email_to_response(email: GraphEmail) -> GraphEmailResponse:
    """Convert GraphEmail to response model"""
    return GraphEmailResponse(
        id=email.id,
        message_id=email.message_id,
        thread_id=email.thread_id,
        subject=email.subject,
        from_address=email.from_address,
        from_name=email.from_name,
        to_address=email.to_address,
        to_name=email.to_name,
        cc_address=email.cc_address,
        body_text=email.body_text,
        body_html=email.body_html,
        date=email.date.isoformat(),
        is_read=email.is_read,
        has_attachments=email.has_attachments,
        folder=email.folder,
        importance=email.importance
    )


@router.get("/emails", response_model=FetchEmailsResponse)
async def fetch_microsoft_emails(
    user_email: EmailStr = Query(..., description="Microsoft account email address"),
    folder: str = Query("inbox", description="Mail folder (inbox, sent, drafts, trash)"),
    max_results: int = Query(50, ge=1, le=100, description="Maximum emails to fetch"),
    skip: int = Query(0, ge=0, description="Number of emails to skip"),
    unread_only: bool = Query(False, description="Only fetch unread emails"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Fetch emails from Microsoft Graph API
    
    This endpoint retrieves emails from the authenticated user's mailbox
    using Microsoft Graph API.
    
    Requires the user to have authenticated via Microsoft OAuth first.
    """
    try:
        logger.info(f"Fetching Microsoft emails for {user_email}, folder={folder}")
        
        emails = await microsoft_graph_client.fetch_emails(
            user_email=user_email,
            db=db,
            folder=folder,
            max_results=max_results,
            skip=skip,
            filter_unread=unread_only
        )
        
        email_responses = [_graph_email_to_response(e) for e in emails]
        
        return FetchEmailsResponse(
            success=True,
            emails=email_responses,
            count=len(email_responses),
            message=f"Fetched {len(email_responses)} emails from {folder}"
        )
    
    except MicrosoftOAuthError as e:
        logger.error(f"Microsoft OAuth error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication error: {e}. Please re-authenticate with Microsoft."
        )
    
    except Exception as e:
        logger.error(f"Error fetching Microsoft emails: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch emails: {e}"
        )


@router.post("/send", response_model=SendEmailResponse)
async def send_microsoft_email(
    request: SendEmailRequest,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Send email via Microsoft Graph API
    
    This endpoint sends an email using the authenticated user's Microsoft account.
    
    Requires the user to have authenticated via Microsoft OAuth first.
    """
    try:
        logger.info(f"Sending Microsoft email from {request.user_email} to {request.to_address}")
        
        result = await microsoft_graph_client.send_email(
            user_email=request.user_email,
            db=db,
            to_address=request.to_address,
            subject=request.subject,
            body_text=request.body_text,
            body_html=request.body_html,
            cc_address=request.cc_address,
            bcc_address=request.bcc_address
        )
        
        return SendEmailResponse(
            success=result.success,
            message_id=result.message_id,
            message=result.message
        )
    
    except MicrosoftOAuthError as e:
        logger.error(f"Microsoft OAuth error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication error: {e}. Please re-authenticate with Microsoft."
        )
    
    except Exception as e:
        logger.error(f"Error sending Microsoft email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {e}"
        )


@router.post("/mark-read")
async def mark_email_read(
    request: MarkReadRequest,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Mark an email as read or unread"""
    try:
        success = await microsoft_graph_client.mark_as_read(
            user_email=request.user_email,
            db=db,
            message_id=request.message_id,
            is_read=request.is_read
        )
        
        if success:
            return {"success": True, "message": f"Email marked as {'read' if request.is_read else 'unread'}"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update email status"
            )
    
    except MicrosoftOAuthError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post("/delete")
async def delete_email(
    request: DeleteEmailRequest,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Delete (move to trash) an email"""
    try:
        success = await microsoft_graph_client.delete_email(
            user_email=request.user_email,
            db=db,
            message_id=request.message_id
        )
        
        if success:
            return {"success": True, "message": "Email moved to trash"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete email"
            )
    
    except MicrosoftOAuthError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.get("/unread-count")
async def get_unread_count(
    user_email: EmailStr = Query(..., description="Microsoft account email address"),
    folder: str = Query("inbox", description="Mail folder"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get count of unread emails in a folder"""
    try:
        count = await microsoft_graph_client.get_unread_count(
            user_email=user_email,
            db=db,
            folder=folder
        )
        
        return {"success": True, "unread_count": count, "folder": folder}
    
    except MicrosoftOAuthError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
