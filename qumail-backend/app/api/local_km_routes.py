"""
Local Key Manager API Routes
============================

REST API endpoints for managing the Local Key Manager:
- View key statistics
- Manually trigger key fetch
- Check key availability
- Clear local keys
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional
import logging

from ..services.local_key_manager import get_local_key_manager, LocalKeyManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/local-km", tags=["Local Key Manager"])


@router.get("/status")
async def get_local_km_status() -> Dict[str, Any]:
    """
    Get Local Key Manager status and statistics
    
    Returns:
        - available_keys: Number of keys ready to use
        - total_keys: Total keys in storage
        - consumed_keys: Keys that have been used
        - expired_keys: Keys that have expired
        - needs_refill: Whether key pool is low
        - auto_fill_enabled: Whether auto-fill is active
    """
    try:
        lkm = get_local_key_manager()
        stats = lkm.get_key_statistics()
        
        return {
            "success": True,
            "status": "healthy" if stats["available_keys"] > 0 else "empty",
            "statistics": stats,
            "config": {
                "min_threshold": lkm.config.MIN_KEYS_THRESHOLD,
                "max_capacity": lkm.config.MAX_KEYS_TO_STORE,
                "keys_per_fetch": lkm.config.KEYS_PER_FETCH,
                "auto_fill_enabled": lkm.config.AUTO_FILL_ENABLED,
                "auto_fill_interval_seconds": lkm.config.AUTO_FILL_INTERVAL_SECONDS,
                "key_expiration_hours": lkm.config.KEY_EXPIRATION_HOURS
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get local KM status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fetch")
async def fetch_keys_from_main_kme(
    count: int = Query(default=None, ge=1, le=100, description="Number of keys to fetch")
) -> Dict[str, Any]:
    """
    Manually trigger key fetch from main KME servers
    
    Args:
        count: Number of keys to fetch (default: configured KEYS_PER_FETCH)
        
    Returns:
        - fetched: Number of keys successfully fetched
        - statistics: Updated key statistics
    """
    try:
        lkm = get_local_key_manager()
        
        logger.info(f"Manual key fetch requested: {count} keys")
        
        fetched = await lkm.fetch_keys_from_main_kme(count)
        stats = lkm.get_key_statistics()
        
        return {
            "success": True,
            "fetched": fetched,
            "requested": count or lkm.config.KEYS_PER_FETCH,
            "statistics": stats,
            "message": f"Successfully fetched {fetched} keys from main KME"
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch keys: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refill")
async def ensure_minimum_keys() -> Dict[str, Any]:
    """
    Ensure local key pool has minimum required keys
    
    Will fetch keys from main KME if pool is below threshold.
    
    Returns:
        - success: Whether operation completed
        - refilled: Whether keys were fetched
        - statistics: Current key statistics
    """
    try:
        lkm = get_local_key_manager()
        
        stats_before = lkm.get_key_statistics()
        
        if stats_before["available_keys"] >= lkm.config.MIN_KEYS_THRESHOLD:
            return {
                "success": True,
                "refilled": False,
                "message": f"Key pool already has sufficient keys ({stats_before['available_keys']})",
                "statistics": stats_before
            }
        
        logger.info("Refilling key pool to minimum threshold...")
        
        result = await lkm.ensure_minimum_keys()
        stats_after = lkm.get_key_statistics()
        
        return {
            "success": True,
            "refilled": True,
            "keys_added": stats_after["available_keys"] - stats_before["available_keys"],
            "statistics": stats_after,
            "message": f"Key pool refilled: {stats_before['available_keys']} -> {stats_after['available_keys']}"
        }
        
    except Exception as e:
        logger.error(f"Failed to refill keys: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cleanup")
async def cleanup_expired_keys() -> Dict[str, Any]:
    """
    Remove expired and consumed keys from local storage
    
    Returns:
        - cleaned: Number of keys removed
        - statistics: Updated key statistics
    """
    try:
        lkm = get_local_key_manager()
        
        cleaned = lkm.cleanup_expired_keys()
        stats = lkm.get_key_statistics()
        
        return {
            "success": True,
            "cleaned": cleaned,
            "statistics": stats,
            "message": f"Cleaned up {cleaned} expired/consumed keys"
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup keys: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/key/{key_id}")
async def check_key_exists(key_id: str) -> Dict[str, Any]:
    """
    Check if a specific key exists in local storage
    
    Args:
        key_id: The key ID to check
        
    Returns:
        - exists: Whether key is in local storage
        - available: Whether key is available for use
    """
    try:
        lkm = get_local_key_manager()
        key_data = lkm.get_key_by_id(key_id)
        
        if key_data:
            return {
                "success": True,
                "exists": True,
                "available": True,
                "key_id": key_id,
                "key_size_bytes": key_data["key_size_bytes"],
                "source": key_data["source"],
                "message": "Key found in local storage"
            }
        else:
            return {
                "success": True,
                "exists": False,
                "available": False,
                "key_id": key_id,
                "message": "Key not found in local storage"
            }
            
    except Exception as e:
        logger.error(f"Failed to check key: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start-autofill")
async def start_auto_fill_service() -> Dict[str, Any]:
    """
    Start the background auto-fill service
    
    The service periodically fetches keys from main KME to maintain
    minimum key pool level.
    """
    try:
        lkm = get_local_key_manager()
        await lkm.start_auto_fill_service()
        
        return {
            "success": True,
            "message": "Auto-fill service started",
            "config": {
                "interval_seconds": lkm.config.AUTO_FILL_INTERVAL_SECONDS,
                "min_threshold": lkm.config.MIN_KEYS_THRESHOLD,
                "keys_per_fetch": lkm.config.KEYS_PER_FETCH
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to start auto-fill service: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop-autofill")
async def stop_auto_fill_service() -> Dict[str, Any]:
    """
    Stop the background auto-fill service
    """
    try:
        lkm = get_local_key_manager()
        await lkm.stop_auto_fill_service()
        
        return {
            "success": True,
            "message": "Auto-fill service stopped"
        }
        
    except Exception as e:
        logger.error(f"Failed to stop auto-fill service: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint for Local Key Manager
    
    Returns:
        - healthy: Overall health status
        - has_keys: Whether local keys are available
        - main_kme_available: Whether main KME can be reached
    """
    try:
        lkm = get_local_key_manager()
        stats = lkm.get_key_statistics()
        
        has_keys = stats["available_keys"] > 0
        above_threshold = stats["available_keys"] >= lkm.config.MIN_KEYS_THRESHOLD
        
        # Try to check main KME availability
        main_kme_available = False
        try:
            lkm._init_km_clients()
            if lkm._km1_client:
                main_kme_available = True
        except:
            pass
        
        health_status = "healthy"
        if not has_keys:
            health_status = "empty" if main_kme_available else "critical"
        elif not above_threshold:
            health_status = "low"
        
        return {
            "healthy": health_status in ["healthy", "low"],
            "status": health_status,
            "has_keys": has_keys,
            "above_threshold": above_threshold,
            "available_keys": stats["available_keys"],
            "min_threshold": lkm.config.MIN_KEYS_THRESHOLD,
            "main_kme_available": main_kme_available
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "healthy": False,
            "status": "error",
            "error": str(e)
        }
