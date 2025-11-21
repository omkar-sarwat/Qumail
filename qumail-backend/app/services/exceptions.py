"""
Custom exceptions for quantum email system
"""

class QuantumEmailError(Exception):
    """Base exception for quantum email operations"""
    pass

class Level1SecurityError(QuantumEmailError):
    """Level 1 OTP specific security errors"""
    pass

class Level2SecurityError(QuantumEmailError):
    """Level 2 AES specific security errors"""
    pass

class Level3SecurityError(QuantumEmailError):
    """Level 3 PQC specific security errors"""
    pass

class Level4SecurityError(QuantumEmailError):
    """Level 4 RSA specific security errors"""
    pass

class InsufficientKeysError(QuantumEmailError):
    """Raised when not enough quantum keys are available"""
    pass

class UnauthorizedAccessError(QuantumEmailError):
    """Raised when user tries to access unauthorized content"""
    pass

class SecurityError(QuantumEmailError):
    """General security-related errors"""
    pass

class TamperingDetectedError(SecurityError):
    """Raised when message tampering is detected"""
    pass

class KeyConsumptionError(QuantumEmailError):
    """Raised when key consumption tracking fails"""
    pass

class QuantumKeyError(QuantumEmailError):
    """Raised when quantum key operations fail"""
    pass

class CertificateError(QuantumEmailError):
    """Raised when certificate operations fail"""
    pass
