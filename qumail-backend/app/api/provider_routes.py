from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import logging

from ..services.provider_registry import detect_provider, list_providers
from ..services.mail_connectivity import test_imap_connection, test_smtp_connection, list_imap_folders, test_pop3_connection

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/providers", tags=["Email Providers"])


class DetectRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")


class ProviderDetection(BaseModel):
    mode: str
    provider: str
    settings: Optional[Dict[str, Any]] = None


class ConnectionConfig(BaseModel):
    host: str
    port: int
    security: str = Field(..., description="ssl or starttls")
    username: str
    password: str

    def normalized_security(self) -> str:
        sec = self.security.lower()
        if sec not in ("ssl", "starttls"):
            raise ValueError("security must be 'ssl' or 'starttls'")
        return sec


@router.post("/detect", response_model=ProviderDetection)
async def detect_provider_settings(payload: DetectRequest):
    try:
        result = detect_provider(payload.email)
        return ProviderDetection(**result)
    except Exception as exc:
        logger.error("Provider detection failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Detection failed")


@router.get("/list", response_model=List[Dict[str, Any]])
async def get_provider_list():
    return list_providers()


@router.post("/test/imap")
async def imap_test(config: ConnectionConfig):
    try:
        security = config.normalized_security()
        result = await test_imap_connection(config.host, config.port, security, config.username, config.password)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as exc:
        logger.error("IMAP test failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"IMAP test failed: {exc}")


@router.post("/test/smtp")
async def smtp_test(config: ConnectionConfig):
    try:
        security = config.normalized_security()
        result = await test_smtp_connection(config.host, config.port, security, config.username, config.password)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as exc:
        logger.error("SMTP test failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"SMTP test failed: {exc}")


@router.post("/test/pop3")
async def pop3_test(config: ConnectionConfig):
    """Test POP3 connection (for providers like Rediffmail that don't support IMAP)"""
    try:
        security = config.normalized_security()
        result = await test_pop3_connection(config.host, config.port, security, config.username, config.password)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as exc:
        logger.error("POP3 test failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"POP3 test failed: {exc}")


@router.post("/folders", response_model=Dict[str, Any])
async def list_folders(config: ConnectionConfig):
    try:
        security = config.normalized_security()
        folders = await list_imap_folders(config.host, config.port, security, config.username, config.password)
        return {"status": "ok", "folders": folders}
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as exc:
        logger.error("Folder list failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Folder listing failed: {exc}")
