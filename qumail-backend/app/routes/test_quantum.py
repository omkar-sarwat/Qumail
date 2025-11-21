"""
Simple Quantum System Test Endpoint
Quick test to verify quantum key generation and encryption is working
"""

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/test", tags=["Testing"])

@router.get("/quantum-check/status")
async def test_quantum_status():
    """Quick test to check if quantum system is operational"""
    try:
        from ..services.km_client_init import get_optimized_km_clients
        from ..services.quantum_key_manager import OneTimeQuantumKeyManager, SecurityLevel
        
        # Test KM client connectivity
        km1_client, km2_client = get_optimized_km_clients()
        
        # Test quantum key manager
        quantum_manager = OneTimeQuantumKeyManager([km1_client, km2_client])
        await quantum_manager.initialize()
        
        # Try to generate a test key
        try:
            key_info = await quantum_manager.get_one_time_key(SecurityLevel.LOW)
            key_generated = key_info is not None
            key_id = key_info['key_id'][:16] + "..." if key_info else "None"
        except Exception as e:
            key_generated = False
            key_id = f"Error: {str(e)}"
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "quantum_system": "operational",
                "timestamp": datetime.utcnow().isoformat(),
                "kme_clients": {
                    "kme1": km1_client.base_url,
                    "kme2": km2_client.base_url
                },
                "test_key_generation": {
                    "success": key_generated,
                    "key_id": key_id
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Quantum system test failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "quantum_system": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

@router.post("/quantum/encrypt")
async def test_quantum_encryption(message: str = "Hello Quantum World!"):
    """Test quantum encryption with a simple message"""
    try:
        from ..services.encryption.level1_otp import encrypt_otp_quantum
        
        # Test encryption
        result = await encrypt_otp_quantum(
            content=message,
            user_email="test@qumail.com"
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "test": "quantum_encryption",
                "success": True,
                "original_message": message,
                "algorithm": result.get("algorithm"),
                "encrypted_length": len(result.get("encrypted_content", "")),
                "key_id": result.get("metadata", {}).get("key_id", "")[:16] + "...",
                "security_level": result.get("metadata", {}).get("security_level"),
                "obfuscated_preview": result.get("obfuscated_preview", "")[:50] + "...",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Quantum encryption test failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "test": "quantum_encryption",
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )