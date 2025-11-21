"""
Draft Management API Routes
Drafts are synced across devices via user's Google account
"""
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
import logging

from ..mongo_database import get_database
from ..mongo_models import UserDocument, DraftDocument
from ..mongo_repositories import DraftRepository, UserRepository
from ..api.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/drafts", tags=["drafts"])

# Request/Response Models
class CreateDraftRequest(BaseModel):
    recipient: Optional[EmailStr] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    security_level: int = 2
    cc: Optional[str] = None
    bcc: Optional[str] = None

class UpdateDraftRequest(BaseModel):
    recipient: Optional[EmailStr] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    security_level: Optional[int] = None
    cc: Optional[str] = None
    bcc: Optional[str] = None

class DraftResponse(BaseModel):
    id: str
    user_email: str
    recipient: Optional[str]
    subject: Optional[str]
    body: Optional[str]
    security_level: int
    cc: Optional[str]
    bcc: Optional[str]
    created_at: str
    updated_at: str
    is_synced: bool

@router.post("/", response_model=DraftResponse)
async def create_draft(
    request: CreateDraftRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserDocument = Depends(get_current_user)
):
    """
    Create a new draft
    
    Drafts are automatically synced across all devices where the user logs in
    with their Google account.
    """
    try:
        draft_repo = DraftRepository(db)
        
        # Create draft linked to user's Google account
        draft_doc = DraftDocument(
            user_id=str(current_user.id),
            user_email=current_user.email,  # Google account email for sync
            recipient=request.recipient,
            subject=request.subject,
            body=request.body,
            security_level=request.security_level,
            cc=request.cc,
            bcc=request.bcc,
            is_synced=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        draft = await draft_repo.create(draft_doc)
        
        logger.info(f"Draft created for {current_user.email}: {draft.id}")
        
        return DraftResponse(
            id=draft.id,
            user_email=draft.user_email,
            recipient=draft.recipient,
            subject=draft.subject,
            body=draft.body,
            security_level=draft.security_level,
            cc=draft.cc,
            bcc=draft.bcc,
            created_at=draft.created_at.isoformat(),
            updated_at=draft.updated_at.isoformat(),
            is_synced=draft.is_synced
        )
        
    except Exception as e:
        logger.error(f"Error creating draft: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create draft: {str(e)}"
        )

@router.get("/", response_model=List[DraftResponse])
async def list_drafts(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserDocument = Depends(get_current_user)
):
    """
    List all drafts for the current user
    
    Returns all drafts associated with the user's Google account,
    regardless of which device they were created on.
    """
    try:
        draft_repo = DraftRepository(db)
        
        # Get all drafts by user email (cross-device sync)
        drafts = await draft_repo.list_by_email(current_user.email)
        
        logger.info(f"Retrieved {len(drafts)} drafts for {current_user.email}")
        
        return [
            DraftResponse(
                id=draft.id,
                user_email=draft.user_email,
                recipient=draft.recipient,
                subject=draft.subject,
                body=draft.body,
                security_level=draft.security_level,
                cc=draft.cc,
                bcc=draft.bcc,
                created_at=draft.created_at.isoformat(),
                updated_at=draft.updated_at.isoformat(),
                is_synced=draft.is_synced
            )
            for draft in drafts
        ]
        
    except Exception as e:
        logger.error(f"Error listing drafts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list drafts: {str(e)}"
        )

@router.get("/{draft_id}", response_model=DraftResponse)
async def get_draft(
    draft_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserDocument = Depends(get_current_user)
):
    """
    Get a specific draft by ID
    
    Only returns the draft if it belongs to the current user's Google account.
    """
    try:
        draft_repo = DraftRepository(db)
        
        # Verify user owns this draft
        draft = await draft_repo.find_by_user_and_id(current_user.email, draft_id)
        
        if not draft:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Draft not found or you don't have permission to access it"
            )
        
        return DraftResponse(
            id=draft.id,
            user_email=draft.user_email,
            recipient=draft.recipient,
            subject=draft.subject,
            body=draft.body,
            security_level=draft.security_level,
            cc=draft.cc,
            bcc=draft.bcc,
            created_at=draft.created_at.isoformat(),
            updated_at=draft.updated_at.isoformat(),
            is_synced=draft.is_synced
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting draft: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get draft: {str(e)}"
        )

@router.put("/{draft_id}", response_model=DraftResponse)
async def update_draft(
    draft_id: str,
    request: UpdateDraftRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserDocument = Depends(get_current_user)
):
    """
    Update a draft
    
    Updates are synced across all devices where the user is logged in.
    """
    try:
        draft_repo = DraftRepository(db)
        
        # Verify user owns this draft
        draft = await draft_repo.find_by_user_and_id(current_user.email, draft_id)
        
        if not draft:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Draft not found or you don't have permission to access it"
            )
        
        # Build updates dict (only include fields that were provided)
        updates = {"updated_at": datetime.utcnow()}
        if request.recipient is not None:
            updates["recipient"] = request.recipient
        if request.subject is not None:
            updates["subject"] = request.subject
        if request.body is not None:
            updates["body"] = request.body
        if request.security_level is not None:
            updates["security_level"] = request.security_level
        if request.cc is not None:
            updates["cc"] = request.cc
        if request.bcc is not None:
            updates["bcc"] = request.bcc
        
        # Update draft
        success = await draft_repo.update(draft_id, updates)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update draft"
            )
        
        # Get updated draft
        updated_draft = await draft_repo.find_by_id(draft_id)
        
        logger.info(f"Draft updated for {current_user.email}: {draft_id}")
        
        return DraftResponse(
            id=updated_draft.id,
            user_email=updated_draft.user_email,
            recipient=updated_draft.recipient,
            subject=updated_draft.subject,
            body=updated_draft.body,
            security_level=updated_draft.security_level,
            cc=updated_draft.cc,
            bcc=updated_draft.bcc,
            created_at=updated_draft.created_at.isoformat(),
            updated_at=updated_draft.updated_at.isoformat(),
            is_synced=updated_draft.is_synced
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating draft: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update draft: {str(e)}"
        )

@router.delete("/{draft_id}")
async def delete_draft(
    draft_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserDocument = Depends(get_current_user)
):
    """
    Delete a draft
    
    Deletion is synced across all devices where the user is logged in.
    """
    try:
        draft_repo = DraftRepository(db)
        
        # Verify user owns this draft
        draft = await draft_repo.find_by_user_and_id(current_user.email, draft_id)
        
        if not draft:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Draft not found or you don't have permission to access it"
            )
        
        # Delete draft
        success = await draft_repo.delete(draft_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete draft"
            )
        
        logger.info(f"Draft deleted for {current_user.email}: {draft_id}")
        
        return {"success": True, "message": "Draft deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting draft: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete draft: {str(e)}"
        )
