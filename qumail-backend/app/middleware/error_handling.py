import logging
import traceback
import uuid
from datetime import datetime
from typing import Union, Dict, Any
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import ValidationError
from ..services.security_auditor import security_auditor, SecurityIncidentType
from ..response_schemas import ErrorResponse

logger = logging.getLogger(__name__)

class SecurityError(Exception):
    """Security-related errors that require special handling"""
    pass

class EncryptionError(Exception):
    """Encryption/decryption related errors"""
    pass

class KMError(Exception):
    """Key Management server related errors"""
    pass

class QuMailHTTPException(HTTPException):
    """Custom HTTP exception with enhanced security logging"""
    
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: str = None,
        user_id: str = None,
        security_incident: bool = False,
        incident_type: SecurityIncidentType = None
    ):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code
        self.user_id = user_id
        self.security_incident = security_incident
        self.incident_type = incident_type or SecurityIncidentType.SYSTEM_ERROR

async def security_exception_handler(request: Request, exc: SecurityError):
    """Handle security-related exceptions with proper logging"""
    request_id = str(uuid.uuid4())
    
    # Log security incident
    await security_auditor.log_incident(
        SecurityIncidentType.SECURITY_ERROR,
        f"Security error: {str(exc)}",
        details={
            "error": str(exc),
            "path": str(request.url),
            "method": request.method,
            "request_id": request_id,
            "client_ip": request.client.host if request.client else "unknown"
        }
    )
    
    logger.error(f"Security error [{request_id}]: {exc}")
    
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content=ErrorResponse(
            error="Security Error",
            detail="A security violation was detected",
            error_code="SECURITY_VIOLATION",
            timestamp=datetime.utcnow().isoformat(),
            request_id=request_id
        ).dict()
    )

async def encryption_exception_handler(request: Request, exc: EncryptionError):
    """Handle encryption-related exceptions"""
    request_id = str(uuid.uuid4())
    
    # Log encryption error
    await security_auditor.log_incident(
        SecurityIncidentType.ENCRYPTION_ERROR,
        f"Encryption error: {str(exc)}",
        details={
            "error": str(exc),
            "path": str(request.url),
            "method": request.method,
            "request_id": request_id
        }
    )
    
    logger.error(f"Encryption error [{request_id}]: {exc}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Encryption Error",
            detail="Encryption operation failed",
            error_code="ENCRYPTION_FAILED",
            timestamp=datetime.utcnow().isoformat(),
            request_id=request_id
        ).dict()
    )

async def km_exception_handler(request: Request, exc: KMError):
    """Handle KM server related exceptions"""
    request_id = str(uuid.uuid4())
    
    # Log KM error
    await security_auditor.log_incident(
        SecurityIncidentType.KM_ERROR,
        f"KM server error: {str(exc)}",
        details={
            "error": str(exc),
            "path": str(request.url),
            "method": request.method,
            "request_id": request_id
        }
    )
    
    logger.error(f"KM server error [{request_id}]: {exc}")
    
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=ErrorResponse(
            error="Key Management Error",
            detail="Key management server unavailable",
            error_code="KM_UNAVAILABLE",
            timestamp=datetime.utcnow().isoformat(),
            request_id=request_id
        ).dict()
    )

async def qumail_http_exception_handler(request: Request, exc: QuMailHTTPException):
    """Handle custom QuMail HTTP exceptions with security logging"""
    request_id = str(uuid.uuid4())
    
    # Log security incident if flagged
    if exc.security_incident:
        await security_auditor.log_incident(
            exc.incident_type,
            f"HTTP error: {exc.detail}",
            user_id=exc.user_id,
            details={
                "status_code": exc.status_code,
                "detail": exc.detail,
                "error_code": exc.error_code,
                "path": str(request.url),
                "method": request.method,
                "request_id": request_id,
                "client_ip": request.client.host if request.client else "unknown"
            }
        )
    
    logger.error(f"HTTP error [{request_id}]: {exc.status_code} - {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error="HTTP Error",
            detail=exc.detail,
            error_code=exc.error_code,
            timestamp=datetime.utcnow().isoformat(),
            request_id=request_id
        ).dict()
    )

async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions with security awareness"""
    request_id = str(uuid.uuid4())
    
    # Get user info from request if available
    user_id = None
    try:
        # Try to extract user from session token in headers or query params
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            from ..services.gmail_oauth import oauth_service
            session_token = auth_header[7:]
            payload = oauth_service.validate_session_token(session_token)
            if payload:
                user_id = payload.get("user_email")
    except Exception:
        pass  # Don't fail on user extraction
    
    # Log system error
    await security_auditor.log_incident(
        SecurityIncidentType.SYSTEM_ERROR,
        f"Unhandled exception: {type(exc).__name__}",
        user_id=user_id,
        details={
            "error": str(exc),
            "error_type": type(exc).__name__,
            "path": str(request.url),
            "method": request.method,
            "request_id": request_id,
            "traceback": traceback.format_exc(),
            "client_ip": request.client.host if request.client else "unknown"
        }
    )
    
    logger.error(f"Unhandled exception [{request_id}]: {type(exc).__name__}: {exc}")
    logger.debug(f"Traceback [{request_id}]: {traceback.format_exc()}")
    
    # Don't expose internal error details in production
    detail = "An internal server error occurred"
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal Server Error",
            detail=detail,
            error_code="INTERNAL_ERROR",
            timestamp=datetime.utcnow().isoformat(),
            request_id=request_id
        ).dict()
    )

async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle Pydantic validation errors with security logging"""
    request_id = str(uuid.uuid4())
    
    # Extract validation errors
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(x) for x in error["loc"])
        message = error["msg"]
        errors.append(f"{field}: {message}")
    
    # Log validation error (potential security issue if excessive)
    await security_auditor.log_incident(
        SecurityIncidentType.VALIDATION_ERROR,
        f"Request validation failed: {len(errors)} errors",
        details={
            "errors": errors,
            "path": str(request.url),
            "method": request.method,
            "request_id": request_id,
            "client_ip": request.client.host if request.client else "unknown"
        }
    )
    
    logger.warning(f"Validation error [{request_id}]: {errors}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error="Validation Error",
            detail=f"Request validation failed: {'; '.join(errors[:3])}",  # Limit exposure
            error_code="VALIDATION_FAILED",
            timestamp=datetime.utcnow().isoformat(),
            request_id=request_id
        ).dict()
    )

# Custom middleware for security headers and logging

class SecurityMiddleware:
    """Security middleware for HTTP headers and request logging"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            
            # Log request for security monitoring
            client_ip = request.client.host if request.client else "unknown"
            user_agent = request.headers.get("user-agent", "unknown")
            
            logger.info(
                f"Request: {request.method} {request.url} from {client_ip} "
                f"User-Agent: {user_agent}"
            )
            
            # Check for suspicious patterns
            await self._check_suspicious_request(request, client_ip)
            
            # Add security headers to response
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    headers = dict(message.get("headers", []))
                    
                    # Add security headers
                    security_headers = {
                        b"x-content-type-options": b"nosniff",
                        b"x-frame-options": b"DENY",
                        b"x-xss-protection": b"1; mode=block",
                        b"strict-transport-security": b"max-age=31536000; includeSubDomains",
                        b"referrer-policy": b"strict-origin-when-cross-origin",
                        b"permissions-policy": b"geolocation=(), microphone=(), camera=()",
                        b"x-qumail-version": b"1.0.0-secure"
                    }
                    
                    # Update headers
                    headers.update(security_headers)
                    message["headers"] = list(headers.items())
                
                await send(message)
            
            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)
    
    async def _check_suspicious_request(self, request: Request, client_ip: str):
        """Check for suspicious request patterns"""
        try:
            path = str(request.url.path).lower()
            query = str(request.url.query).lower() if request.url.query else ""
            
            # Check for common attack patterns
            suspicious_patterns = [
                "admin", "wp-admin", "phpmyadmin", "mysql", 
                "shell", "cmd", "exec", "eval", "script",
                "javascript:", "vbscript:", "onload", "onerror",
                "union", "select", "insert", "delete", "drop",
                "../", "..\\", "etc/passwd", "windows/system32"
            ]
            
            suspicious_detected = False
            for pattern in suspicious_patterns:
                if pattern in path or pattern in query:
                    suspicious_detected = True
                    break
            
            # Check for excessive requests (simple rate limiting indication)
            if suspicious_detected:
                await security_auditor.log_incident(
                    SecurityIncidentType.SUSPICIOUS_ACTIVITY,
                    f"Suspicious request pattern detected from {client_ip}",
                    details={
                        "path": path,
                        "query": query,
                        "client_ip": client_ip,
                        "user_agent": request.headers.get("user-agent", "unknown")
                    }
                )
        
        except Exception as e:
            logger.error(f"Error checking suspicious request: {e}")

# Rate limiting middleware (basic implementation)

class RateLimitMiddleware:
    """Basic rate limiting middleware"""
    
    def __init__(self, app, requests_per_minute: int = 300):
        self.app = app
        self.requests_per_minute = requests_per_minute
        self.client_requests = {}  # In production, use Redis
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            client_ip = request.client.host if request.client else "unknown"
            
            # Check rate limit
            if await self._is_rate_limited(client_ip):
                # Send rate limit response
                request_id = str(uuid.uuid4())
                response = JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content=ErrorResponse(
                        error="Rate Limit Exceeded",
                        detail="Too many requests from this IP address",
                        error_code="RATE_LIMITED",
                        timestamp=datetime.utcnow().isoformat(),
                        request_id=request_id
                    ).dict()
                )
                await response(scope, receive, send)
                return
        
        await self.app(scope, receive, send)
    
    async def _is_rate_limited(self, client_ip: str) -> bool:
        """Check if client IP is rate limited"""
        try:
            current_time = datetime.utcnow()
            
            # Clean old entries
            self.client_requests = {
                ip: requests for ip, requests in self.client_requests.items()
                if any(req_time > current_time - timedelta(minutes=1) for req_time in requests)
            }
            
            # Get client requests in last minute
            if client_ip not in self.client_requests:
                self.client_requests[client_ip] = []
            
            # Filter recent requests
            recent_requests = [
                req_time for req_time in self.client_requests[client_ip]
                if req_time > current_time - timedelta(minutes=1)
            ]
            
            # Check limit
            if len(recent_requests) >= self.requests_per_minute:
                # Log rate limit violation
                await security_auditor.log_incident(
                    SecurityIncidentType.RATE_LIMIT_EXCEEDED,
                    f"Rate limit exceeded for IP {client_ip}",
                    details={
                        "client_ip": client_ip,
                        "requests_in_minute": len(recent_requests),
                        "limit": self.requests_per_minute
                    }
                )
                return True
            
            # Add current request
            recent_requests.append(current_time)
            self.client_requests[client_ip] = recent_requests
            
            return False
        
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            return False  # Allow request on error

# Import fix
from datetime import timedelta