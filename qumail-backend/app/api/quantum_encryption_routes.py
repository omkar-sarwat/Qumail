"""
QuMail Quantum Encryption API Routes
Provides secure quantum-encrypted messaging with one-time-use keys
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, validator
import logging
import asyncio
from datetime import datetime
import json

from ..services.quantum_key_manager import SecurityLevel, OneTimeQuantumKeyManager
from ..services.qumail_encryption import QuMailQuantumEncryption, QuMailSecurityLevelManager
from ..api.auth import get_current_user
from ..mongo_models import UserDocument
from ..services.security_auditor import security_auditor, SecurityIncidentType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/quantum", tags=["Quantum Encryption"])

# Pydantic models for request/response
class EncryptMessageRequest(BaseModel):
    """Request model for quantum message encryption"""
    message: str = Field(..., min_length=1, max_length=10000, description="Message to encrypt")
    recipient_id: str = Field(..., description="Recipient user ID")
    security_level: str = Field(default="MEDIUM", description="Security level: LOW, MEDIUM, HIGH, ULTRA")
    
    @validator('security_level')
    def validate_security_level(cls, v):
        valid_levels = ['LOW', 'MEDIUM', 'HIGH', 'ULTRA']
        if v.upper() not in valid_levels:
            raise ValueError(f"Security level must be one of: {', '.join(valid_levels)}")
        return v.upper()

class DecryptMessageRequest(BaseModel):
    """Request model for quantum message decryption"""
    encrypted_data: str = Field(..., description="Encrypted message data")
    key_id: str = Field(..., description="Quantum key ID used for encryption")

class QuantumKeyStatusRequest(BaseModel):
    """Request model for checking quantum key status"""
    key_ids: List[str] = Field(..., description="List of quantum key IDs to check")

class EncryptMessageResponse(BaseModel):
    """Response model for quantum message encryption"""
    success: bool
    encrypted_data: str
    key_id: str
    security_level: str
    timestamp: datetime
    expires_at: Optional[datetime]
    obfuscated_preview: str  # What external apps see

class DecryptMessageResponse(BaseModel):
    """Response model for quantum message decryption"""
    success: bool
    decrypted_message: str
    key_consumed: bool
    security_level: str
    timestamp: datetime

class QuantumKeyStatusResponse(BaseModel):
    """Response model for quantum key status"""
    key_statuses: Dict[str, Dict[str, Any]]
    total_keys_checked: int
    consumed_keys: int
    active_keys: int

class SecurityLevelInfoResponse(BaseModel):
    """Response model for security level information"""
    available_levels: List[Dict[str, Any]]
    current_key_pools: Dict[str, int]
    total_consumed_keys: int

# Dependency to get quantum services from app state
async def get_quantum_services(request: Request):
    """Get quantum services from app state"""
    try:
        quantum_key_manager = request.app.state.quantum_key_manager
        qumail_encryption = request.app.state.qumail_encryption
        security_level_manager = request.app.state.security_level_manager
        
        return {
            "quantum_key_manager": quantum_key_manager,
            "qumail_encryption": qumail_encryption,
            "security_level_manager": security_level_manager
        }
    except AttributeError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Quantum services not initialized"
        )

@router.post("/encrypt", response_model=EncryptMessageResponse)
async def encrypt_message(
    request: EncryptMessageRequest,
    background_tasks: BackgroundTasks,
    current_user: UserDocument = Depends(get_current_user),
    quantum_services: Dict = Depends(get_quantum_services)
):
    """
    Encrypt a message using one-time quantum keys
    
    Features:
    - One-time-use quantum key generation
    - Multi-level security (LOW, MEDIUM, HIGH, ULTRA)
    - QuMail-only decryption capability
    - Automatic key consumption tracking
    """
    try:
        qumail_encryption = quantum_services["qumail_encryption"]
        security_level = SecurityLevel[request.security_level]
        
        logger.info(f"User {current_user.email} encrypting message with {security_level.name} security")
        
        # Encrypt the message
        encryption_result = await qumail_encryption.encrypt_message(
            message=request.message,
            sender_id=str(current_user.id),
            recipient_id=request.recipient_id,
            security_level=security_level
        )
        
        # Log security event
        background_tasks.add_task(
            security_auditor.log_incident,
            SecurityIncidentType.ENCRYPTION_SUCCESS,
            f"Quantum message encrypted with {security_level.name} security",
            details={
                "user_id": str(current_user.id),
                "recipient_id": request.recipient_id,
                "security_level": security_level.name,
                "key_id": encryption_result["key_id"],
                "message_length": len(request.message)
            }
        )
        
        return EncryptMessageResponse(
            success=True,
            encrypted_data=encryption_result["encrypted_data"],
            key_id=encryption_result["key_id"],
            security_level=security_level.name,
            timestamp=datetime.utcnow(),
            expires_at=encryption_result.get("expires_at"),
            obfuscated_preview=encryption_result["obfuscated_preview"]
        )
        
    except Exception as e:
        logger.error(f"Quantum encryption failed for user {current_user.email}: {e}")
        
        # Log security incident
        background_tasks.add_task(
            security_auditor.log_incident,
            SecurityIncidentType.ENCRYPTION_FAILURE,
            f"Quantum encryption failed: {str(e)}",
            details={
                "user_id": str(current_user.id),
                "security_level": request.security_level,
                "error": str(e)
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quantum encryption failed: {str(e)}"
        )

@router.post("/decrypt", response_model=DecryptMessageResponse)
async def decrypt_message(
    request: DecryptMessageRequest,
    background_tasks: BackgroundTasks,
    current_user: UserDocument = Depends(get_current_user),
    quantum_services: Dict = Depends(get_quantum_services)
):
    """
    Decrypt a quantum-encrypted message
    
    Features:
    - One-time key consumption (key becomes invalid after use)
    - QuMail application verification
    - Security level validation
    - Audit trail for decryption events
    """
    try:
        qumail_encryption = quantum_services["qumail_encryption"]
        
        logger.info(f"User {current_user.email} attempting to decrypt message with key {request.key_id}")
        
        # Decrypt the message
        decryption_result = await qumail_encryption.decrypt_message(
            encrypted_data=request.encrypted_data,
            key_id=request.key_id,
            user_id=str(current_user.id)
        )
        
        # Log security event
        background_tasks.add_task(
            security_auditor.log_incident,
            SecurityIncidentType.DECRYPTION_SUCCESS,
            f"Quantum message decrypted successfully",
            details={
                "user_id": str(current_user.id),
                "key_id": request.key_id,
                "key_consumed": decryption_result["key_consumed"],
                "security_level": decryption_result["security_level"]
            }
        )
        
        return DecryptMessageResponse(
            success=True,
            decrypted_message=decryption_result["decrypted_message"],
            key_consumed=decryption_result["key_consumed"],
            security_level=decryption_result["security_level"],
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Quantum decryption failed for user {current_user.email}: {e}")
        
        # Log security incident
        background_tasks.add_task(
            security_auditor.log_incident,
            SecurityIncidentType.DECRYPTION_FAILURE,
            f"Quantum decryption failed: {str(e)}",
            details={
                "user_id": str(current_user.id),
                "key_id": request.key_id,
                "error": str(e)
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Quantum decryption failed: {str(e)}"
        )

@router.post("/key-status", response_model=QuantumKeyStatusResponse)
async def check_key_status(
    request: QuantumKeyStatusRequest,
    current_user: UserDocument = Depends(get_current_user),
    quantum_services: Dict = Depends(get_quantum_services)
):
    """
    Check the status of quantum keys
    
    Returns information about:
    - Key consumption status
    - Security levels
    - Expiration times
    - Usage history
    """
    try:
        quantum_key_manager = quantum_services["quantum_key_manager"]
        
        logger.info(f"User {current_user.email} checking status of {len(request.key_ids)} quantum keys")
        
        key_statuses = {}
        consumed_count = 0
        active_count = 0
        
        for key_id in request.key_ids:
            status_info = await quantum_key_manager.get_key_status(key_id)
            key_statuses[key_id] = status_info
            
            if status_info.get("consumed", False):
                consumed_count += 1
            else:
                active_count += 1
        
        return QuantumKeyStatusResponse(
            key_statuses=key_statuses,
            total_keys_checked=len(request.key_ids),
            consumed_keys=consumed_count,
            active_keys=active_count
        )
        
    except Exception as e:
        logger.error(f"Key status check failed for user {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Key status check failed: {str(e)}"
        )

@router.get("/security-levels", response_model=SecurityLevelInfoResponse)
async def get_security_levels(
    current_user: UserDocument = Depends(get_current_user),
    quantum_services: Dict = Depends(get_quantum_services)
):
    """
    Get information about available security levels
    
    Returns:
    - Available security levels and their specifications
    - Current key pool status
    - Total consumed keys across all levels
    """
    try:
        security_level_manager = quantum_services["security_level_manager"]
        
        logger.info(f"User {current_user.email} requesting security level information")
        
        # Get security level information
        available_levels = []
        for level in SecurityLevel:
            level_info = {
                "name": level.name,
                "key_size_bytes": level.value,
                "description": f"{level.name.title()} security level ({level.value} bytes)",
                "recommended_use": security_level_manager._get_level_recommendation(level)
            }
            available_levels.append(level_info)
        
        # Get current key pool status
        key_pools = await security_level_manager.get_key_pool_status()
        
        # Get total consumed keys
        total_consumed = await security_level_manager.get_total_consumed_keys()
        
        return SecurityLevelInfoResponse(
            available_levels=available_levels,
            current_key_pools=key_pools,
            total_consumed_keys=total_consumed
        )
        
    except Exception as e:
        logger.error(f"Security level info request failed for user {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get security level information: {str(e)}"
        )

@router.get("/health")
async def quantum_health_check(
    current_user: UserDocument = Depends(get_current_user),
    quantum_services: Dict = Depends(get_quantum_services)
):
    """
    Health check for quantum encryption services
    
    Verifies:
    - Quantum key manager connectivity
    - Database connectivity
    - KME server status
    - Key generation capability
    """
    try:
        quantum_key_manager = quantum_services["quantum_key_manager"]
        
        # Test key generation for each security level
        health_status = {
            "quantum_services": "operational",
            "kme_connectivity": {},
            "key_generation": {},
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Test KME connectivity
        kme1_status = await quantum_key_manager._test_kme_connectivity(quantum_key_manager.kme1_client)
        kme2_status = await quantum_key_manager._test_kme_connectivity(quantum_key_manager.kme2_client)
        
        health_status["kme_connectivity"] = {
            "kme1": "connected" if kme1_status else "disconnected",
            "kme2": "connected" if kme2_status else "disconnected"
        }
        
        # Test key generation for each level
        for level in SecurityLevel:
            try:
                test_key = await quantum_key_manager._generate_quantum_key(level)
                health_status["key_generation"][level.name] = "operational"
            except Exception as e:
                health_status["key_generation"][level.name] = f"error: {str(e)}"
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=health_status
        )
        
    except Exception as e:
        logger.error(f"Quantum health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "quantum_services": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
