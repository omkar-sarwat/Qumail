"""
Security configuration for QuMail Quantum Security System
Defines security levels and cryptographic parameters
"""

from enum import Enum
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class SecurityLevel(Enum):
    """
    Security levels for quantum key sizes and encryption strength
    Each level corresponds to specific key sizes and security requirements
    """
    LOW = 32          # 256-bit keys - Basic security for routine communications
    MEDIUM = 64       # 512-bit keys - Standard business communications  
    HIGH = 128        # 1024-bit keys - Confidential and sensitive data
    ULTRA = 256       # 2048-bit keys - Top secret and classified information
    CLASSIFIED = 512  # 4096-bit keys - Maximum security for intelligence operations

    @property
    def key_size_bytes(self) -> int:
        """Get key size in bytes for this security level"""
        return self.value
    
    @property
    def key_size_bits(self) -> int:
        """Get key size in bits for this security level"""
        return self.value * 8
    
    @property
    def description(self) -> str:
        """Get human-readable description of security level"""
        descriptions = {
            SecurityLevel.LOW: "Basic security for routine communications",
            SecurityLevel.MEDIUM: "Standard business communications", 
            SecurityLevel.HIGH: "Confidential and sensitive data",
            SecurityLevel.ULTRA: "Top secret and classified information",
            SecurityLevel.CLASSIFIED: "Maximum security for intelligence operations"
        }
        return descriptions.get(self, "Unknown security level")
    
    @property
    def min_entropy_score(self) -> float:
        """Minimum entropy score required for this security level"""
        entropy_requirements = {
            SecurityLevel.LOW: 0.7,
            SecurityLevel.MEDIUM: 0.75,
            SecurityLevel.HIGH: 0.8,
            SecurityLevel.ULTRA: 0.85,
            SecurityLevel.CLASSIFIED: 0.9
        }
        return entropy_requirements.get(self, 0.5)
    
    @classmethod
    def from_string(cls, level_str: str) -> Optional['SecurityLevel']:
        """Convert string to SecurityLevel enum"""
        try:
            return cls[level_str.upper()]
        except KeyError:
            logger.warning(f"Invalid security level: {level_str}")
            return None
    
    @classmethod
    def get_all_levels(cls) -> Dict[str, 'SecurityLevel']:
        """Get all available security levels"""
        return {level.name: level for level in cls}

class QuantumSecurityConfig:
    """
    Configuration parameters for quantum security operations
    """
    
    # Key generation parameters
    DEFAULT_KEY_LIFETIME_HOURS = 24
    MAX_KEY_REUSE_ATTEMPTS = 0  # Zero = one-time use only
    
    # Encryption parameters
    QUMAIL_SIGNATURE_PREFIX = "QM_QUANTUM_"
    GIBBERISH_CHARSET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_+-=[]{}|;:,.<>?"
    MIN_GIBBERISH_LENGTH = 64
    
    # KME server configuration
    KME_REQUEST_TIMEOUT_SECONDS = 30
    KME_HEALTH_CHECK_INTERVAL_MINUTES = 5
    KME_MAX_RETRY_ATTEMPTS = 3
    
    # Database configuration
    QUANTUM_DB_RETENTION_DAYS = 90
    KEY_AUDIT_LOG_RETENTION_DAYS = 365
    
    # Performance thresholds
    MAX_KEY_GENERATION_TIME_MS = 5000
    MAX_DATABASE_QUERY_TIME_MS = 1000
    MAX_MEMORY_USAGE_PERCENT = 80
    
    # Security validation
    SECURITY_VALIDATION_INTERVAL_HOURS = 6
    ENTROPY_ANALYSIS_SAMPLE_SIZE = 1024
    
    @classmethod
    def get_security_config(cls, security_level: SecurityLevel) -> Dict[str, Any]:
        """Get complete security configuration for a specific level"""
        return {
            "security_level": security_level.name,
            "key_size_bytes": security_level.key_size_bytes,
            "key_size_bits": security_level.key_size_bits,
            "min_entropy_score": security_level.min_entropy_score,
            "description": security_level.description,
            "key_lifetime_hours": cls.DEFAULT_KEY_LIFETIME_HOURS,
            "max_reuse_attempts": cls.MAX_KEY_REUSE_ATTEMPTS,
            "validation_requirements": {
                "entropy_check": True,
                "one_time_use": True,
                "perfect_forward_secrecy": True,
                "qumail_exclusivity": True
            }
        }
    
    @classmethod
    def validate_security_parameters(cls, security_level: SecurityLevel, 
                                   key_material: bytes, entropy_score: float) -> Dict[str, bool]:
        """Validate that security parameters meet requirements"""
        validation_results = {
            "key_size_valid": len(key_material) >= security_level.key_size_bytes,
            "entropy_sufficient": entropy_score >= security_level.min_entropy_score,
            "key_material_present": key_material is not None and len(key_material) > 0
        }
        
        validation_results["overall_valid"] = all(validation_results.values())
        return validation_results

# Default KME server configurations for different environments
KME_SERVER_CONFIGS = {
    "development": [
        {
            "server_url": "https://localhost:8010",
            "cert_file": "certs/kme-1-local-zone/client_1.crt",
            "key_file": "certs/kme-1-local-zone/client_1.key",
            "ca_file": "certs/kme-1-local-zone/ca.crt"
        },
        {
            "server_url": "https://localhost:8020", 
            "cert_file": "certs/kme-2-local-zone/client_3.crt",
            "key_file": "certs/kme-2-local-zone/client_3.key",
            "ca_file": "certs/kme-2-local-zone/ca.crt"
        }
    ],
    "production": [
        {
            "server_url": "https://kme-primary.qumail.com",
            "cert_file": "/etc/qumail/certs/client.crt",
            "key_file": "/etc/qumail/certs/client.key",
            "ca_file": "/etc/qumail/certs/ca.crt"
        },
        {
            "server_url": "https://kme-secondary.qumail.com",
            "cert_file": "/etc/qumail/certs/client.crt", 
            "key_file": "/etc/qumail/certs/client.key",
            "ca_file": "/etc/qumail/certs/ca.crt"
        }
    ]
}

# Security validation schedules
VALIDATION_SCHEDULES = {
    "continuous": {
        "key_generation_validation": "every_key",
        "system_health_check": "every_5_minutes",
        "security_audit": "every_hour"
    },
    "standard": {
        "key_generation_validation": "every_10_keys", 
        "system_health_check": "every_15_minutes",
        "security_audit": "every_6_hours"
    },
    "minimal": {
        "key_generation_validation": "every_100_keys",
        "system_health_check": "every_hour", 
        "security_audit": "daily"
    }
}