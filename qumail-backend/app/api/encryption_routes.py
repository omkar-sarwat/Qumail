from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Dict, Any
import logging
from ..mongo_database import get_database
from ..services.gmail_oauth import oauth_service
from ..services.security_auditor import security_auditor, SecurityIncidentType
from ..request_schemas import EncryptionRequest, DecryptionRequest, KMStatusRequest
from ..response_schemas import (
    EncryptionResponse, 
    DecryptionResponse, 
    KMStatusResponse,
    SecurityLevelValidationResponse
)
from ..schemas import SecurityLevel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/encryption", tags=["Encryption"])

@router.post("/encrypt", response_model=EncryptionResponse)
async def encrypt_content(
    request: EncryptionRequest,
    background_tasks: BackgroundTasks,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Encrypt content using specified security level
    
    Security Features:
    - Multiple encryption algorithms (OTP, Q-AES, PQC, RSA)
    - Quantum key integration
    - Digital signatures
    - Comprehensive audit logging
    """
    try:
        # Validate security level
        try:
            security_level = SecurityLevel(request.security_level)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid security level: {request.security_level}"
            )
        
        # Apply encryption based on security level
        encrypted_result = None
        
        if security_level == SecurityLevel.LEVEL_1:
            # One-Time Quantum Pad encryption with one-time-use keys
            from ..services.encryption.level1_otp import encrypt_otp
            encrypted_result = await encrypt_otp(request.content, request.user_email)
            
        elif security_level == SecurityLevel.LEVEL_2:
            # Quantum-enhanced AES encryption with quantum keys
            from ..services.encryption.level2_aes import encrypt_aes
            encrypted_result = await encrypt_aes(request.content, request.user_email)
            
        elif security_level == SecurityLevel.LEVEL_3:
            # Post-quantum cryptography with quantum key enhancement
            from ..services.encryption.level3_pqc import encrypt_pqc
            encrypted_result = await encrypt_pqc(request.content, request.user_email)
            
        elif security_level == SecurityLevel.LEVEL_4:
            # High-security RSA with quantum key seeding
            from ..services.encryption.level4_rsa import encrypt_rsa
            encrypted_result = await encrypt_rsa(request.content, request.user_email)
        
        if not encrypted_result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Encryption failed"
            )
        
        # Log encryption event
        background_tasks.add_task(
            security_auditor.log_incident,
            SecurityIncidentType.ENCRYPTION_USED,
            f"Content encrypted with {security_level.value}",
            user_id=request.user_email,
            details={
                "security_level": security_level.value,
                "content_size": len(request.content),
                "algorithm": encrypted_result.get("algorithm", "unknown"),
                "metadata": encrypted_result.get("metadata", {})
            }
        )
        
        logger.info(f"Content encrypted with {security_level.value} for {request.user_email}")
        
        return EncryptionResponse(
            encrypted_content=encrypted_result["encrypted_content"],
            security_level=security_level.value,
            encryption_algorithm=encrypted_result.get("algorithm", "unknown"),
            signature=encrypted_result.get("signature", ""),
            metadata=encrypted_result.get("metadata", {}),
            success=True
        )
    
    except Exception as e:
        logger.error(f"Encryption error: {e}")
        await security_auditor.log_incident(
            SecurityIncidentType.ENCRYPTION_ERROR,
            f"Encryption failed: {str(e)}",
            user_id=request.user_email,
            details={"error": str(e), "security_level": request.security_level}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Encryption failed: {str(e)}"
        )

@router.post("/decrypt", response_model=DecryptionResponse)
async def decrypt_content(
    request: DecryptionRequest,
    background_tasks: BackgroundTasks,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Decrypt content using specified security level
    
    Security Features:
    - Signature verification
    - Tampering detection
    - Secure key derivation
    - Audit logging
    """
    try:
        # Validate security level
        try:
            security_level = SecurityLevel(request.security_level)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid security level: {request.security_level}"
            )
        
        # Apply decryption based on security level
        decrypted_result = None
        
        if security_level == SecurityLevel.LEVEL_1:
            # One-Time Pad decryption
            from ..services.encryption.level1_otp import decrypt_otp
            decrypted_result = await decrypt_otp(
                request.encrypted_content, 
                request.user_email, 
                request.metadata or {}
            )
            
        elif security_level == SecurityLevel.LEVEL_2:
            # Quantum-enhanced AES decryption
            from ..services.encryption.level2_aes import decrypt_aes
            decrypted_result = await decrypt_aes(
                request.encrypted_content, 
                request.user_email, 
                request.metadata or {}
            )
            
        elif security_level == SecurityLevel.LEVEL_3:
            # Post-quantum cryptography decryption
            from ..services.encryption.level3_pqc import decrypt_pqc
            decrypted_result = await decrypt_pqc(
                request.encrypted_content, 
                request.user_email, 
                request.metadata or {}
            )
            
        elif security_level == SecurityLevel.LEVEL_4:
            # Standard RSA decryption
            from ..services.encryption.level4_rsa import decrypt_rsa
            decrypted_result = await decrypt_rsa(
                request.encrypted_content, 
                request.user_email, 
                request.metadata or {}
            )
        
        if not decrypted_result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Decryption failed"
            )
        
        # Check for tampering
        tampering_detected = not decrypted_result.get("signature_valid", True)
        if tampering_detected:
            await security_auditor.log_incident(
                SecurityIncidentType.TAMPERING_DETECTED,
                f"Message tampering detected during {security_level.value} decryption",
                user_id=request.user_email,
                details={
                    "security_level": security_level.value,
                    "signature_valid": decrypted_result.get("signature_valid", False),
                    "metadata": request.metadata
                }
            )
        
        # Log decryption event
        background_tasks.add_task(
            security_auditor.log_incident,
            SecurityIncidentType.DECRYPTION_USED,
            f"Content decrypted with {security_level.value}",
            user_id=request.user_email,
            details={
                "security_level": security_level.value,
                "signature_valid": decrypted_result.get("signature_valid", True),
                "tampering_detected": tampering_detected
            }
        )
        
        logger.info(f"Content decrypted with {security_level.value} for {request.user_email}")
        
        return DecryptionResponse(
            decrypted_content=decrypted_result["decrypted_content"],
            security_level=security_level.value,
            signature_valid=decrypted_result.get("signature_valid", True),
            tampering_detected=tampering_detected,
            success=True,
            message="Decryption successful" if not tampering_detected else "Decryption successful but tampering detected"
        )
    
    except Exception as e:
        logger.error(f"Decryption error: {e}")
        await security_auditor.log_incident(
            SecurityIncidentType.DECRYPTION_ERROR,
            f"Decryption failed: {str(e)}",
            user_id=request.user_email,
            details={"error": str(e), "security_level": request.security_level}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Decryption failed: {str(e)}"
        )

@router.post("/km-status", response_model=KMStatusResponse)
async def check_km_status(
    request: KMStatusRequest,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Check KM server status and available keys
    
    Returns:
        Status of both KM servers and available key counts
    """
    try:
        # Check KM server status using optimized KM client
        from ..services.km_client_init import get_optimized_km_clients
        km1_client, km2_client = get_optimized_km_clients()
        
        # Check KM server 1
        kme1_status = "unknown"
        kme1_keys = 0
        try:
            status1 = await km1_client.check_key_status("c565d5aa-8670-4446-8471-b0e53e315d2a")
            kme1_status = "healthy" if status1.get("stored_key_count", 0) > 0 else "unhealthy"
            kme1_keys = status1.get("stored_key_count", 0)
        except Exception as e:
            logger.warning(f"KM1 status check failed: {e}")
            kme1_status = "error"
        
        # Check KM server 2
        kme2_status = "unknown"
        kme2_keys = 0
        try:
            status2 = await km2_client.check_key_status("25840139-0dd4-49ae-ba1e-b86731601803")
            kme2_status = "healthy" if status2.get("stored_key_count", 0) > 0 else "unhealthy"
            kme2_keys = status2.get("stored_key_count", 0)
        except Exception as e:
            logger.warning(f"KM2 status check failed: {e}")
            kme2_status = "error"
        
        # Overall health
        connection_healthy = kme1_status == "healthy" and kme2_status == "healthy"
        
        from datetime import datetime
        
        return KMStatusResponse(
            kme1_status=kme1_status,
            kme2_status=kme2_status,
            kme1_available_keys=kme1_keys,
            kme2_available_keys=kme2_keys,
            last_check=datetime.utcnow().isoformat(),
            connection_healthy=connection_healthy
        )
    
    except Exception as e:
        logger.error(f"KM status check error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check KM status: {str(e)}"
        )

@router.get("/levels", response_model=Dict[str, Any])
async def get_security_levels():
    """
    Get available security levels and their descriptions
    
    Returns:
        Dictionary of security levels with detailed descriptions
    """
    return {
        "security_levels": {
            "LEVEL_1": {
                "name": "Quantum One-Time Pad",
                "description": "Perfect secrecy using quantum keys from both KM servers",
                "algorithm": "One-Time Pad with quantum key combination",
                "key_source": "Quantum keys from KME1 and KME2",
                "signature": "RSA-PSS with SHA-256",
                "security_rating": "Maximum",
                "use_case": "Ultra-sensitive communications requiring perfect secrecy"
            },
            "LEVEL_2": {
                "name": "Quantum-Enhanced AES",
                "description": "AES-256-GCM with quantum-derived keys",
                "algorithm": "AES-256-GCM with HKDF key derivation",
                "key_source": "Quantum keys from both KM servers",
                "signature": "RSA-PSS with SHA-256",
                "security_rating": "Very High",
                "use_case": "High-security business communications"
            },
            "LEVEL_3": {
                "name": "Post-Quantum Cryptography",
                "description": "Quantum-resistant cryptographic algorithms",
                "algorithm": "Kyber1024 + Dilithium5 + AES-256-GCM",
                "key_source": "Kyber KEM with quantum key enhancement",
                "signature": "Dilithium5 post-quantum signatures",
                "security_rating": "Future-Proof High",
                "use_case": "Future-proof communications against quantum computers"
            },
            "LEVEL_4": {
                "name": "Standard RSA",
                "description": "Traditional RSA encryption with modern security",
                "algorithm": "RSA-4096-OAEP + AES-256-GCM",
                "key_source": "RSA key pairs with HKDF session keys",
                "signature": "RSA-PSS with SHA-256",
                "security_rating": "Standard High",
                "use_case": "General secure communications and fallback option"
            }
        },
        "recommendations": {
            "maximum_security": "LEVEL_1",
            "business_default": "LEVEL_2",
            "future_proof": "LEVEL_3",
            "compatibility": "LEVEL_4"
        },
        "security_features": [
            "End-to-end encryption",
            "Digital signatures",
            "Tampering detection",
            "Perfect forward secrecy",
            "Quantum key management",
            "Security incident logging"
        ]
    }

@router.post("/validate-level", response_model=SecurityLevelValidationResponse)
async def validate_security_level(
    security_level: str,
    user_email: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Validate and get details about a security level for a user
    
    Args:
        security_level: The security level to validate
        user_email: User email for capability checking
    
    Returns:
        Validation results and security level details
    """
    try:
        # Validate security level
        try:
            level = SecurityLevel(security_level)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid security level: {security_level}"
            )
        
        # Security features based on level
        security_features = []
        encryption_algorithm = ""
        key_sources = []
        signature_algorithm = "RSA-PSS with SHA-256"
        additional_protections = []
        
        if level == SecurityLevel.LEVEL_1:
            security_features = ["Perfect Secrecy", "Quantum Keys", "Dual KM Sources"]
            encryption_algorithm = "One-Time Pad"
            key_sources = ["KME1 Quantum Keys", "KME2 Quantum Keys"]
            additional_protections = ["Information-theoretic security", "Unconditional security"]
            
        elif level == SecurityLevel.LEVEL_2:
            security_features = ["AES-256-GCM", "Quantum Key Derivation", "HKDF"]
            encryption_algorithm = "AES-256-GCM"
            key_sources = ["KME1 Quantum Keys", "KME2 Quantum Keys"]
            additional_protections = ["Authenticated encryption", "Quantum-enhanced keys"]
            
        elif level == SecurityLevel.LEVEL_3:
            security_features = ["Post-Quantum KEM", "Quantum-Resistant Signatures", "AES-256-GCM"]
            encryption_algorithm = "Kyber1024 + AES-256-GCM"
            key_sources = ["Kyber1024 KEM", "Quantum Key Enhancement"]
            signature_algorithm = "Dilithium5"
            additional_protections = ["Quantum computer resistance", "NIST PQC algorithms"]
            
        elif level == SecurityLevel.LEVEL_4:
            security_features = ["RSA-4096", "OAEP Padding", "AES-256-GCM Session"]
            encryption_algorithm = "RSA-4096-OAEP + AES-256-GCM"
            key_sources = ["RSA Key Pairs", "HKDF Session Keys"]
            additional_protections = ["Hybrid encryption", "Session key security"]
        
        return SecurityLevelValidationResponse(
            requested_level=security_level,
            applied_level=security_level,
            security_features=security_features,
            encryption_algorithm=encryption_algorithm,
            key_sources=key_sources,
            signature_algorithm=signature_algorithm,
            additional_protections=additional_protections
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Security level validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation failed: {str(e)}"
        )
