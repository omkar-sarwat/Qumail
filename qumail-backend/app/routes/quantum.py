"""
Routes for QKD KME server integration
"""
import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Dict, Any, List, Optional

from ..mongo_database import get_database
from ..api.auth import get_current_user
from ..mongo_models import UserDocument
from ..services.kme_service import kme_service, KmeServiceError
from ..services.real_qkd_client import real_kme1_client, real_kme2_client

router = APIRouter(prefix="/api/v1/quantum", tags=["quantum"])
logger = logging.getLogger(__name__)

@router.get("/status")
async def get_quantum_status() -> Dict[str, Any]:
    """Get status of quantum key distribution systems"""
    try:
        # Get status from KME service first
        kme_status = await kme_service.get_system_status()
        
        # Add status from the real QKD clients
        qkd_status = {}
        
        # Check KME1 client
        if real_kme1_client:
            try:
                kme1_status = await real_kme1_client.get_real_status()
                qkd_status["kme1"] = kme1_status
            except Exception as e:
                logger.error(f"Failed to get KME1 status: {e}")
                qkd_status["kme1"] = {"status": "error", "message": str(e)}
        else:
            qkd_status["kme1"] = {"status": "unavailable", "message": "KME1 client not initialized"}
            
        # Check KME2 client
        if real_kme2_client:
            try:
                kme2_status = await real_kme2_client.get_real_status()
                qkd_status["kme2"] = kme2_status
            except Exception as e:
                logger.error(f"Failed to get KME2 status: {e}")
                qkd_status["kme2"] = {"status": "error", "message": str(e)}
        else:
            qkd_status["kme2"] = {"status": "unavailable", "message": "KME2 client not initialized"}
        
        # Calculate system status
        system_status = "operational"
        if kme_status["system_status"] != "operational":
            system_status = "degraded"
        if qkd_status.get("kme1", {}).get("status") != "connected" and qkd_status.get("kme2", {}).get("status") != "connected":
            system_status = "critical"
            
        # Combine all status information
        combined_status = {
            **kme_status,
            "qkd_clients": qkd_status,
            "system_status": system_status
        }
        
        return combined_status
    except Exception as e:
        logger.error(f"Error getting quantum status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get quantum status: {str(e)}")

@router.get("/keys/available")
async def get_available_keys() -> Dict[str, Any]:
    """Get available quantum keys"""
    try:
        keys = []
        
        # Get keys from KME1
        if real_kme1_client:
            try:
                available_keys = real_kme1_client.get_available_quantum_keys()
                for key_path in available_keys[:10]:  # Limit to 10 keys
                    keys.append({
                        "id": key_path.split('/')[-1],
                        "kme": "kme1",
                        "type": "quantum",
                        "path": key_path
                    })
            except Exception as e:
                logger.error(f"Error getting KME1 keys: {e}")
        
        # Get keys from KME2
        if real_kme2_client:
            try:
                available_keys = real_kme2_client.get_available_quantum_keys()
                for key_path in available_keys[:10]:  # Limit to 10 keys
                    keys.append({
                        "id": key_path.split('/')[-1],
                        "kme": "kme2",
                        "type": "quantum",
                        "path": key_path
                    })
            except Exception as e:
                logger.error(f"Error getting KME2 keys: {e}")
        
        return {
            "keys": keys,
            "count": len(keys),
            "available": len(keys) > 0
        }
    except Exception as e:
        logger.error(f"Error getting available keys: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get available keys: {str(e)}")

@router.post("/test/connection")
async def test_quantum_connection(
    request: Request
) -> Dict[str, Any]:
    """Test connection to quantum KME servers"""
    try:
        data = await request.json()
        kme_id = data.get("kme_id", 1)
        
        try:
            # Try to connect to the KME
            client_info = await kme_service.get_client_info(kme_id)
            
            # Get key status and entropy info
            slave_sae_id = 2 if kme_id == 1 else 1
            key_status = await kme_service.get_key_status(kme_id, slave_sae_id)
            entropy_info = await kme_service.get_entropy_info(kme_id)
            
            # Test successfully getting an encryption key
            enc_keys = await kme_service.get_encryption_keys(kme_id, slave_sae_id, 1)
            
            return {
                "status": "connected",
                "kme_id": kme_id,
                "sae_id": client_info.get("SAE_ID"),
                "stored_key_count": key_status.get("stored_key_count", 0),
                "total_entropy": entropy_info.get("total_entropy", 0),
                "encryption_keys_available": len(enc_keys) > 0,
                "timestamp": key_status.get("timestamp")
            }
        except KmeServiceError as e:
            return {
                "status": "error",
                "kme_id": kme_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    except Exception as e:
        logger.error(f"Error testing quantum connection: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to test connection: {str(e)}")

@router.post("/key/exchange")
async def exchange_quantum_key(
    request: Request
) -> Dict[str, Any]:
    """Exchange a quantum key between KME servers"""
    try:
        data = await request.json()
        sender_kme_id = data.get("sender_kme_id", 1)
        recipient_kme_id = data.get("recipient_kme_id", 2)
        
        try:
            # Exchange a quantum key
            key_id, key_bytes = await kme_service.exchange_quantum_key(
                sender_kme_id, recipient_kme_id
            )
            
            return {
                "status": "success",
                "key_id": key_id,
                "key_length": len(key_bytes),
                "sender_kme_id": sender_kme_id,
                "recipient_kme_id": recipient_kme_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        except KmeServiceError as e:
            return {
                "status": "error",
                "error": str(e),
                "sender_kme_id": sender_kme_id,
                "recipient_kme_id": recipient_kme_id,
                "timestamp": datetime.utcnow().isoformat()
            }
    except Exception as e:
        logger.error(f"Error exchanging quantum key: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to exchange quantum key: {str(e)}")

@router.post("/generate-keys")
async def generate_quantum_keys(
    count: int = 10,
    kme_ids: Optional[List[int]] = None
) -> Dict[str, Any]:
    """
    Generate new quantum keys on KME servers using REAL ETSI QKD 014 API
    This calls the actual /enc_keys endpoint to request keys from the quantum key pool
    """
    try:
        if kme_ids is None:
            kme_ids = [1, 2]  # Default to both KME servers
            
        if not kme_ids:
            kme_ids = [1, 2]  # Default to both KME servers
        
        from datetime import datetime
        
        # Initialize results matching test expectations
        results = {
            "success": True,
            "requestedKeys": count,  # Total keys requested (test expects this to match count param)
            "kme1": {"generated": 0, "successful": 0, "failedKeys": 0, "successRate": 0.0},
            "kme2": {"generated": 0, "successful": 0, "failedKeys": 0, "successRate": 0.0},
            "total": {"generated": 0, "successful": 0, "failedKeys": 0, "successRate": 0.0},
            "keyTimestamps": [],
            "generatedAt": datetime.utcnow().isoformat() + "Z"
        }
        
        # Generate keys for each KME using REAL KME service
        for kme_id in kme_ids:
            try:
                # Call REAL KME service to request keys from quantum pool via /enc_keys
                generated_keys = await kme_service.generate_keys(kme_id, count)
                
                successful_count = len(generated_keys)
                failed_count = count - successful_count
                success_rate = successful_count / count if count > 0 else 0.0
                
                # Record results for this KME
                kme_key = f"kme{kme_id}"
                results[kme_key] = {
                    "generated": successful_count,
                    "successful": successful_count,
                    "failedKeys": failed_count,
                    "successRate": success_rate
                }
                
                # Add timestamps for each key
                for key in generated_keys:
                    results["keyTimestamps"].append(datetime.utcnow().isoformat() + "Z")
                
                # Update totals
                results["total"]["generated"] += successful_count
                results["total"]["successful"] += successful_count
                results["total"]["failedKeys"] += failed_count
                
                logger.info(f"Generated {successful_count} REAL quantum keys from KME {kme_id}")
                
            except Exception as e:
                logger.error(f"Error generating keys on KME {kme_id}: {e}", exc_info=True)
                # Record failure for this KME
                kme_key = f"kme{kme_id}"
                results[kme_key] = {
                    "generated": 0,
                    "successful": 0,
                    "failedKeys": count,
                    "successRate": 0.0,
                    "error": str(e)
                }
                results["total"]["failedKeys"] += count
                results["success"] = False
        
        # Calculate overall success rate
        total_requested = count * len(kme_ids)
        if total_requested > 0:
            results["total"]["successRate"] = results["total"]["successful"] / total_requested
        else:
            results["total"]["successRate"] = 0.0
        
        # Overall success is true if at least some keys were generated
        results["success"] = results["total"]["successful"] > 0
        
        return results
    except Exception as e:
        logger.error(f"Error generating quantum keys: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate quantum keys: {str(e)}")
