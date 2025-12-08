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
    host: str = Field(..., min_length=1, description="Mail server hostname")
    port: int = Field(..., gt=0, le=65535, description="Mail server port")
    security: str = Field(..., description="ssl or starttls")
    username: str = Field(..., min_length=1, description="Login username/email")
    password: str = Field(..., min_length=1, description="Login password")
    timeout: int = Field(30, gt=0, le=90, description="Connection timeout seconds")

    def normalized_security(self) -> str:
        sec = self.security.lower()
        if sec not in ("ssl", "starttls"):
            raise ValueError("security must be 'ssl' or 'starttls'")
        return sec
    
    def validate_host(self) -> str:
        """Return trimmed host, raise if empty after trimming."""
        h = self.host.strip()
        if not h:
            raise ValueError("Host cannot be empty")
        return h


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
        result = await test_imap_connection(
            config.host,
            config.port,
            security,
            config.username,
            config.password,
            timeout=float(config.timeout),
        )
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
        result = await test_smtp_connection(
            config.host,
            config.port,
            security,
            config.username,
            config.password,
            timeout=float(config.timeout),
        )
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
        result = await test_pop3_connection(
            config.host,
            config.port,
            security,
            config.username,
            config.password,
            timeout=float(config.timeout),
        )
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
        folders = await list_imap_folders(
            config.host,
            config.port,
            security,
            config.username,
            config.password,
            timeout=float(config.timeout),
        )
        return {"status": "ok", "folders": folders}
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as exc:
        logger.error("Folder list failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Folder listing failed: {exc}")


@router.get("/test/smtp2go")
async def test_smtp2go_relay():
    """
    Test SMTP2GO relay connection from server (Render).
    Uses env vars: SMTP_RELAY_HOST, SMTP_RELAY_PORT, SMTP_RELAY_USERNAME, SMTP_RELAY_PASSWORD
    """
    import os
    import aiosmtplib
    
    host = os.getenv("SMTP_RELAY_HOST", "mail.smtp2go.com")
    port = int(os.getenv("SMTP_RELAY_PORT", "2525"))
    security = os.getenv("SMTP_RELAY_SECURITY", "starttls").lower()
    username = os.getenv("SMTP_RELAY_USERNAME", "")
    password = os.getenv("SMTP_RELAY_PASSWORD", "")
    
    if not username or not password:
        return {
            "status": "error",
            "message": "SMTP_RELAY_USERNAME and SMTP_RELAY_PASSWORD env vars not set",
            "host": host,
            "port": port,
        }
    
    results = []
    ports_to_try = [
        (port, security == "ssl", security == "starttls"),
        (2525, False, True),
        (8025, False, True),
        (587, False, True),
        (465, True, False),
    ]
    # Remove duplicates
    seen = set()
    unique_ports = []
    for p in ports_to_try:
        if p[0] not in seen:
            seen.add(p[0])
            unique_ports.append(p)
    
    working_port = None
    for test_port, use_tls, start_tls in unique_ports:
        try:
            smtp = aiosmtplib.SMTP(
                hostname=host,
                port=test_port,
                use_tls=use_tls,
                start_tls=start_tls,
                timeout=20,
                validate_certs=False,
            )
            await smtp.connect()
            await smtp.ehlo()
            await smtp.login(username, password)
            await smtp.quit()
            results.append({"port": test_port, "status": "ok", "use_tls": use_tls, "start_tls": start_tls})
            working_port = test_port
            break
        except Exception as e:
            results.append({"port": test_port, "status": "failed", "error": f"{type(e).__name__}: {str(e)}"})
    
    return {
        "status": "ok" if working_port else "all_failed",
        "working_port": working_port,
        "host": host,
        "username": username,
        "tests": results,
    }
