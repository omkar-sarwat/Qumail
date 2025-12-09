"""
QKD (Quantum Key Distribution) API Routes
Provides endpoints for viewing QKD keys, sessions, and audit logs stored in MongoDB.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from ..mongo_database import get_database
from ..mongo_models import UserDocument
from ..api.auth import get_current_user
from ..mongo_repositories import (
    QKDKeyRepository,
    QKDSessionRepository,
    QKDAuditLogRepository,
    QKDKeyPoolStatusRepository
)

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/qkd", tags=["QKD"])


@router.get("/statistics")
async def get_qkd_statistics(
    current_user: UserDocument = Depends(get_current_user),
    db: Any = Depends(get_database)
) -> Dict[str, Any]:
    """
    Get QKD key and session statistics from MongoDB.
    Shows total keys, key states, and session counts.
    """
    try:
        key_repo = QKDKeyRepository(db)
        session_repo = QKDSessionRepository(db)
        
        key_stats = await key_repo.get_statistics()
        session_stats = await session_repo.get_session_statistics()
        
        return {
            "success": True,
            "keys": key_stats,
            "sessions": session_stats,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting QKD statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/keys")
async def list_qkd_keys(
    limit: int = Query(50, ge=1, le=500),
    include_consumed: bool = Query(False),
    security_level: Optional[int] = Query(None, ge=1, le=4),
    current_user: UserDocument = Depends(get_current_user),
    db: Any = Depends(get_database)
) -> Dict[str, Any]:
    """
    List QKD keys from MongoDB.
    By default, shows only available (non-consumed) keys.
    """
    try:
        key_repo = QKDKeyRepository(db)
        
        # Get keys for current user
        keys = await key_repo.get_keys_by_user(
            current_user.email,
            include_consumed=include_consumed
        )
        
        # Filter by security level if specified
        if security_level:
            keys = [k for k in keys if k.security_level == security_level]
        
        # Limit results
        keys = keys[:limit]
        
        # Convert to dicts and remove sensitive data
        key_list = []
        for key in keys:
            key_dict = key.dict()
            # Don't expose actual key material
            if 'key_material_encrypted' in key_dict:
                key_dict['key_material_encrypted'] = '[REDACTED]' if key_dict['key_material_encrypted'] else None
            key_list.append(key_dict)
        
        return {
            "success": True,
            "count": len(key_list),
            "keys": key_list
        }
    except Exception as e:
        logger.error(f"Error listing QKD keys: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/keys/{key_id}")
async def get_qkd_key_details(
    key_id: str,
    current_user: UserDocument = Depends(get_current_user),
    db: Any = Depends(get_database)
) -> Dict[str, Any]:
    """
    Get details of a specific QKD key.
    """
    try:
        key_repo = QKDKeyRepository(db)
        audit_repo = QKDAuditLogRepository(db)
        
        key = await key_repo.find_by_key_id(key_id)
        
        if not key:
            raise HTTPException(status_code=404, detail="Key not found")
        
        # Verify user has access to this key
        if key.sender_email != current_user.email and key.receiver_email != current_user.email:
            raise HTTPException(status_code=403, detail="Access denied to this key")
        
        # Get audit logs for this key
        audit_logs = await audit_repo.find_by_key_id(key_id)
        
        key_dict = key.dict()
        # Don't expose actual key material
        key_dict['key_material_encrypted'] = '[REDACTED]' if key_dict.get('key_material_encrypted') else None
        
        return {
            "success": True,
            "key": key_dict,
            "audit_logs": [log.dict() for log in audit_logs[:20]]  # Last 20 logs
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting QKD key details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/keys/flow/{flow_id}")
async def get_keys_by_flow(
    flow_id: str,
    current_user: UserDocument = Depends(get_current_user),
    db: Any = Depends(get_database)
) -> Dict[str, Any]:
    """
    Get all QKD keys associated with a specific flow ID (email).
    """
    try:
        key_repo = QKDKeyRepository(db)
        keys = await key_repo.find_by_flow_id(flow_id)
        
        # Filter to only show keys the user has access to
        accessible_keys = [
            k for k in keys 
            if k.sender_email == current_user.email or k.receiver_email == current_user.email
        ]
        
        key_list = []
        for key in accessible_keys:
            key_dict = key.dict()
            key_dict['key_material_encrypted'] = '[REDACTED]' if key_dict.get('key_material_encrypted') else None
            key_list.append(key_dict)
        
        return {
            "success": True,
            "flow_id": flow_id,
            "count": len(key_list),
            "keys": key_list
        }
    except Exception as e:
        logger.error(f"Error getting keys by flow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions")
async def list_qkd_sessions(
    limit: int = Query(50, ge=1, le=200),
    active_only: bool = Query(False),
    current_user: UserDocument = Depends(get_current_user),
    db: Any = Depends(get_database)
) -> Dict[str, Any]:
    """
    List QKD sessions from MongoDB.
    """
    try:
        session_repo = QKDSessionRepository(db)
        
        if active_only:
            sessions = await session_repo.find_active_sessions(current_user.email)
        else:
            # Get all sessions for this user
            cursor = session_repo.collection.find({
                "$or": [
                    {"sender_email": current_user.email},
                    {"receiver_email": current_user.email}
                ]
            }).sort("started_at", -1).limit(limit)
            docs = await cursor.to_list(length=None)
            from ..mongo_models import QKDSessionDocument
            sessions = [QKDSessionDocument(**doc) for doc in docs]
        
        return {
            "success": True,
            "count": len(sessions),
            "sessions": [s.dict() for s in sessions]
        }
    except Exception as e:
        logger.error(f"Error listing QKD sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}")
async def get_qkd_session_details(
    session_id: str,
    current_user: UserDocument = Depends(get_current_user),
    db: Any = Depends(get_database)
) -> Dict[str, Any]:
    """
    Get details of a specific QKD session.
    """
    try:
        session_repo = QKDSessionRepository(db)
        key_repo = QKDKeyRepository(db)
        audit_repo = QKDAuditLogRepository(db)
        
        session = await session_repo.find_by_session_id(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Verify user has access
        if session.sender_email != current_user.email and session.receiver_email != current_user.email:
            raise HTTPException(status_code=403, detail="Access denied to this session")
        
        # Get keys used in this session
        keys = []
        for key_id in session.key_ids:
            key = await key_repo.find_by_key_id(key_id)
            if key:
                key_dict = key.dict()
                key_dict['key_material_encrypted'] = '[REDACTED]' if key_dict.get('key_material_encrypted') else None
                keys.append(key_dict)
        
        # Get audit logs
        audit_logs = await audit_repo.find_by_session_id(session_id)
        
        return {
            "success": True,
            "session": session.dict(),
            "keys": keys,
            "audit_logs": [log.dict() for log in audit_logs[:50]]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting QKD session details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit-logs")
async def list_qkd_audit_logs(
    hours: int = Query(24, ge=1, le=168),
    limit: int = Query(100, ge=1, le=500),
    operation: Optional[str] = Query(None),
    errors_only: bool = Query(False),
    current_user: UserDocument = Depends(get_current_user),
    db: Any = Depends(get_database)
) -> Dict[str, Any]:
    """
    List QKD audit logs from MongoDB.
    Can filter by operation type, time range, and errors.
    """
    try:
        audit_repo = QKDAuditLogRepository(db)
        
        if errors_only:
            logs = await audit_repo.find_errors(limit=limit)
        elif operation:
            logs = await audit_repo.find_by_operation(operation, limit=limit)
        else:
            logs = await audit_repo.find_recent(hours=hours, limit=limit)
        
        # Filter to only show logs for current user
        user_logs = [
            log for log in logs
            if log.user_email == current_user.email or not log.user_email
        ]
        
        return {
            "success": True,
            "count": len(user_logs),
            "logs": [log.dict() for log in user_logs]
        }
    except Exception as e:
        logger.error(f"Error listing QKD audit logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pool-status")
async def get_qkd_pool_status(
    current_user: UserDocument = Depends(get_current_user),
    db: Any = Depends(get_database)
) -> Dict[str, Any]:
    """
    Get QKD key pool status for all KME servers.
    """
    try:
        pool_repo = QKDKeyPoolStatusRepository(db)
        statuses = await pool_repo.get_all_status()
        
        return {
            "success": True,
            "pools": [s.dict() for s in statuses],
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting QKD pool status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup-expired")
async def cleanup_expired_keys(
    current_user: UserDocument = Depends(get_current_user),
    db: Any = Depends(get_database)
) -> Dict[str, Any]:
    """
    Trigger cleanup of expired QKD keys.
    Admin operation - marks expired keys in MongoDB.
    """
    try:
        key_repo = QKDKeyRepository(db)
        audit_repo = QKDAuditLogRepository(db)
        
        expired_count = await key_repo.cleanup_expired_keys()
        
        if expired_count > 0:
            await audit_repo.log_operation(
                operation="EXPIRED_KEYS_CLEANUP",
                user_email=current_user.email,
                success=True,
                details={"expired_count": expired_count}
            )
        
        return {
            "success": True,
            "expired_keys_cleaned": expired_count,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error cleaning up expired keys: {e}")
        raise HTTPException(status_code=500, detail=str(e))
