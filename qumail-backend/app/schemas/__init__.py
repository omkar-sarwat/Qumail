"""Common schemas and enums used across the application."""
import enum

class EmailDirection(str, enum.Enum):
    """Email direction enum."""
    SENT = "SENT"
    RECEIVED = "RECEIVED"

class SecurityLevel(str, enum.Enum):
    """Security level enum for encryption."""
    LEVEL_1 = "LEVEL_1"  # Quantum OTP (One-Time Pad) - Perfect secrecy
    LEVEL_2 = "LEVEL_2"  # Quantum AES - Symmetric encryption with quantum keys
    LEVEL_3 = "LEVEL_3"  # Post-Quantum Cryptography - Quantum-resistant algorithms
    LEVEL_4 = "LEVEL_4"  # Standard RSA - Traditional public key cryptography

class IncidentType(str, enum.Enum):
    """Security incident types for logging and tracking"""
    # System events
    SYSTEM_STARTUP = "SYSTEM_STARTUP"
    SYSTEM_SHUTDOWN = "SYSTEM_SHUTDOWN"
    SYSTEM_ERROR = "SYSTEM_ERROR"
    
    # Authentication events
    AUTH_FAILURE = "AUTH_FAILURE"
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    
    # API events
    API_ERROR = "API_ERROR"
    
    # Email events
    EMAIL_SENT = "EMAIL_SENT"
    
    # Encryption events
    ENCRYPTION_USED = "ENCRYPTION_USED"
    ENCRYPTION_SUCCESS = "ENCRYPTION_SUCCESS"
    ENCRYPTION_FAILURE = "ENCRYPTION_FAILURE"
    ENCRYPTION_ERROR = "ENCRYPTION_ERROR"
    DECRYPTION_USED = "DECRYPTION_USED"
    DECRYPTION_ERROR = "DECRYPTION_ERROR"
    
    # Security events
    SECURITY_ERROR = "SECURITY_ERROR"
    TAMPERING_DETECTED = "TAMPERING_DETECTED"
    
    # Key management events
    KM_ERROR = "KM_ERROR"
    
    # Validation events
    VALIDATION_ERROR = "VALIDATION_ERROR"
    
    # Activity monitoring
    SUSPICIOUS_ACTIVITY = "SUSPICIOUS_ACTIVITY"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"

class Severity(str, enum.Enum):
    """Severity levels for security incidents"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

__all__ = ['EmailDirection', 'SecurityLevel', 'IncidentType', 'Severity']
