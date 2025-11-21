"""
KM Status API for QuMail Backend

Provides real-time information about Key Management Entity status,
available keys, and SAE information from Next Door Key Simulator.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from ..services.km_client_init import get_optimized_km_clients
from ..middleware.error_handling import KMError, SecurityError
from ..services.audit_logger import audit_logger, AuditEventType

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/km", tags=["Key Management"])

@router.get("/status", response_model=Dict[str, Any])
async def get_km_status():
    """
    Get comprehensive status of both KME servers from Next Door Key Simulator
    
    Returns:
        Dictionary containing status of both KMEs, available keys, and configuration
    """
    try:
        # Get optimized KM clients
        km1_client, km2_client = get_optimized_km_clients()
        
        # Initialize status structure
        status_response = {
            "timestamp": datetime.utcnow().isoformat(),
            "simulator_type": "Next Door Key Simulator",
            "etsi_standard": "ETSI GS QKD 014 V1.1.1",
            "kme_servers": {}
        }
        
        # Get KME 1 status
        try:
            # KME1 is asked about its peer SAE (c565d5aa... which is attached to KME2)
            kme1_status = await km1_client.check_key_status("c565d5aa-8670-4446-8471-b0e53e315d2a")
            
            # Get KME info
            async with km1_client._get_client() as client:
                kme_info_response = await client.get("/api/v1/kme/status")
                kme1_info = kme_info_response.json()
            
            status_response["kme_servers"]["kme1"] = {
                "url": km1_client.base_url,
                "kme_id": kme1_info.get("KME_ID"),
                "local_sae_id": km1_client.sae_id,
                "peer_sae_id": "c565d5aa-8670-4446-8471-b0e53e315d2a",
                "status": "online",
                "available_keys": kme1_status.get("stored_key_count", 0),
                "max_keys_per_request": kme1_status.get("max_key_per_request", 0),
                "max_key_size": kme1_status.get("max_key_size", 0),
                "min_key_size": kme1_status.get("min_key_size", 0),
                "default_key_size": kme1_status.get("key_size", 0),
                "last_check": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get KME1 status: {e}")
            status_response["kme_servers"]["kme1"] = {
                "url": km1_client.base_url,
                "local_sae_id": km1_client.sae_id,
                "status": "offline",
                "error": str(e),
                "last_check": datetime.utcnow().isoformat()
            }
        
        # Get KME 2 status
        try:
            # KME2 is asked about its peer SAE (25840139... which is attached to KME1)
            kme2_status = await km2_client.check_key_status("25840139-0dd4-49ae-ba1e-b86731601803")
            
            # Get KME info
            async with km2_client._get_client() as client:
                kme_info_response = await client.get("/api/v1/kme/status")
                kme2_info = kme_info_response.json()
            
            status_response["kme_servers"]["kme2"] = {
                "url": km2_client.base_url,
                "kme_id": kme2_info.get("KME_ID"),
                "local_sae_id": km2_client.sae_id,
                "peer_sae_id": "25840139-0dd4-49ae-ba1e-b86731601803",
                "status": "online",
                "available_keys": kme2_status.get("stored_key_count", 0),
                "max_keys_per_request": kme2_status.get("max_key_per_request", 0),
                "max_key_size": kme2_status.get("max_key_size", 0),
                "min_key_size": kme2_status.get("min_key_size", 0),
                "default_key_size": kme2_status.get("key_size", 0),
                "last_check": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get KME2 status: {e}")
            status_response["kme_servers"]["kme2"] = {
                "url": km2_client.base_url,
                "local_sae_id": km2_client.sae_id,
                "status": "offline",
                "error": str(e),
                "last_check": datetime.utcnow().isoformat()
            }
        
        # Calculate totals
        total_keys = sum([
            kme.get("available_keys", 0) for kme in status_response["kme_servers"].values()
            if kme.get("status") == "online"
        ])
        
        online_kmes = sum([
            1 for kme in status_response["kme_servers"].values()
            if kme.get("status") == "online"
        ])
        
        status_response["summary"] = {
            "total_available_keys": total_keys,
            "online_kmes": online_kmes,
            "total_kmes": 2,
            "system_health": "healthy" if online_kmes == 2 else "degraded" if online_kmes > 0 else "offline"
        }
        
        # Log audit event
        await audit_logger.log_event(
            AuditEventType.QUANTUM_KEY_REQUESTED,
            details={"action": "km_status_check", "online_kmes": online_kmes, "total_keys": total_keys}
        )
        
        return status_response
        
    except Exception as e:
        logger.error(f"Failed to get KM status: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Key Management system unavailable: {str(e)}"
        )

@router.get("/keys/available", response_model=Dict[str, Any])
async def get_available_keys_detailed():
    """
    Get detailed information about available quantum keys from both KMEs
    
    Returns:
        Detailed breakdown of available keys per KME with metadata
    """
    try:
        # Get optimized KM clients
        km1_client, km2_client = get_optimized_km_clients()
        
        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "kme_keys": {}
        }
        
        # Get detailed key information from KME 1
        try:
            kme1_status = await km1_client.check_key_status("c565d5aa-8670-4446-8471-b0e53e315d2a")
            result["kme_keys"]["kme1"] = {
                "kme_url": km1_client.base_url,
                "local_sae_id": km1_client.sae_id,
                "peer_sae_id": "c565d5aa-8670-4446-8471-b0e53e315d2a",
                "available_keys": kme1_status.get("stored_key_count", 0),
                "max_per_request": kme1_status.get("max_key_per_request", 0),
                "key_size_bytes": kme1_status.get("key_size", 0),
                "max_key_size": kme1_status.get("max_key_size", 0),
                "min_key_size": kme1_status.get("min_key_size", 0),
                "status": "online"
            }
        except Exception as e:
            result["kme_keys"]["kme1"] = {
                "kme_url": km1_client.base_url,
                "status": "offline",
                "error": str(e)
            }
        
        # Get detailed key information from KME 2
        try:
            kme2_status = await km2_client.check_key_status("25840139-0dd4-49ae-ba1e-b86731601803")
            result["kme_keys"]["kme2"] = {
                "kme_url": km2_client.base_url,
                "local_sae_id": km2_client.sae_id,
                "peer_sae_id": "25840139-0dd4-49ae-ba1e-b86731601803",
                "available_keys": kme2_status.get("stored_key_count", 0),
                "max_per_request": kme2_status.get("max_key_per_request", 0),
                "key_size_bytes": kme2_status.get("key_size", 0),
                "max_key_size": kme2_status.get("max_key_size", 0),
                "min_key_size": kme2_status.get("min_key_size", 0),
                "status": "online"
            }
        except Exception as e:
            result["kme_keys"]["kme2"] = {
                "kme_url": km2_client.base_url,
                "status": "offline",
                "error": str(e)
            }
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to get available keys: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Key Management system unavailable: {str(e)}"
        )

@router.post("/keys/request-test", response_model=Dict[str, Any])
async def request_test_keys(number_of_keys: int = 1):
    """
    Request test quantum keys from KME (for testing purposes only)
    
    Args:
        number_of_keys: Number of keys to request (1-5)
    
    Returns:
        Information about requested keys (without exposing actual key data)
    """
    try:
        if number_of_keys < 1 or number_of_keys > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Number of keys must be between 1 and 5"
            )
        
        # Get optimized KM clients
        km1_client, km2_client = get_optimized_km_clients()
        
        # Request keys from KME 1
        keys = await km1_client.request_enc_keys(
            slave_sae_id="c565d5aa-8670-4446-8471-b0e53e315d2a",
            number=number_of_keys,
            size=256
        )
        
        # Return metadata only (never expose actual key data)
        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "requested_keys": number_of_keys,
            "received_keys": len(keys),
            "keys_metadata": [
                {
                    "key_id": key.get("key_ID"),
                    "key_size_bits": len(key.get("key", "")) * 8 // 4 * 3,  # Estimate from base64
                    "source_kme": km1_client.base_url
                }
                for key in keys
            ]
        }
        
        # Log audit event
        await audit_logger.log_event(
            AuditEventType.QUANTUM_KEY_REQUESTED,
            details={
                "action": "test_key_request", 
                "requested": number_of_keys, 
                "received": len(keys),
                "key_ids": [key.get("key_ID") for key in keys]
            }
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to request test keys: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Test key request failed: {str(e)}"
        )