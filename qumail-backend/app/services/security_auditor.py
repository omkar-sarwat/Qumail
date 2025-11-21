import logging
import json
import traceback
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum
from ..schemas import IncidentType, Severity

# Alias for backward compatibility
SecurityIncidentType = IncidentType

logger = logging.getLogger(__name__)

class SecurityEventType(Enum):
    """Security event types for monitoring and alerting"""
    TAMPERING_DETECTED = "TAMPERING_DETECTED"
    SIGNATURE_INVALID = "SIGNATURE_INVALID" 
    DECRYPTION_FAILED = "DECRYPTION_FAILED"
    KEY_NOT_FOUND = "KEY_NOT_FOUND"
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    INSUFFICIENT_KEYS = "INSUFFICIENT_KEYS"
    LOW_ENTROPY_DETECTED = "LOW_ENTROPY_DETECTED"
    UNAUTHORIZED_ACCESS = "UNAUTHORIZED_ACCESS"
    BRUTE_FORCE_ATTEMPT = "BRUTE_FORCE_ATTEMPT"
    SUSPICIOUS_ACTIVITY = "SUSPICIOUS_ACTIVITY"

class SecurityAuditor:
    """Comprehensive security incident logging and monitoring"""
    
    def __init__(self):
        self.logger = logging.getLogger("qumail.security")
        # Create dedicated security logger with higher level
        self.logger.setLevel(logging.WARNING)
    
    async def log_incident(
        self,
        incident_type: SecurityIncidentType,
        message: str,
        user_id: Optional[str] = None,
        flow_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        session: Optional[Any] = None
    ) -> str:
        """
        Simple incident logging method compatible with existing code
        
        Returns incident ID for tracking
        """
        # Map incident type to severity
        severity_mapping = {
            SecurityIncidentType.SYSTEM_STARTUP: Severity.LOW,
            SecurityIncidentType.SYSTEM_SHUTDOWN: Severity.LOW,
            SecurityIncidentType.SYSTEM_ERROR: Severity.HIGH,
            SecurityIncidentType.AUTH_FAILURE: Severity.HIGH,
            SecurityIncidentType.AUTHENTICATION_FAILED: Severity.HIGH,
            SecurityIncidentType.API_ERROR: Severity.MEDIUM,
            SecurityIncidentType.EMAIL_SENT: Severity.LOW,
            SecurityIncidentType.ENCRYPTION_USED: Severity.LOW,
            SecurityIncidentType.ENCRYPTION_ERROR: Severity.HIGH,
            SecurityIncidentType.DECRYPTION_USED: Severity.LOW,
            SecurityIncidentType.DECRYPTION_ERROR: Severity.HIGH,
            SecurityIncidentType.SECURITY_ERROR: Severity.HIGH,
            SecurityIncidentType.TAMPERING_DETECTED: Severity.CRITICAL,
            SecurityIncidentType.KM_ERROR: Severity.HIGH,
            SecurityIncidentType.VALIDATION_ERROR: Severity.MEDIUM,
            SecurityIncidentType.SUSPICIOUS_ACTIVITY: Severity.MEDIUM,
            SecurityIncidentType.RATE_LIMIT_EXCEEDED: Severity.MEDIUM,
        }
        
        severity = severity_mapping.get(incident_type, Severity.MEDIUM)
        
        # Generate incident ID
        from uuid import uuid4
        incident_id = str(uuid4())
        
        # Log to security logger
        log_level = self._get_log_level(severity)
        self.logger.log(
            log_level,
            f"SECURITY INCIDENT [{severity.value}] {incident_type.value}: "
            f"ID={incident_id}, User={user_id}, Flow={flow_id}, Message={message}"
        )
        
        # Log detailed info at debug level
        if details:
            logger.debug(f"Incident {incident_id} details: {json.dumps(details)}")
        
        return incident_id

    async def log_security_incident(
        self,
        event_type: SecurityEventType,
        severity: Severity,
        user_email: Optional[str] = None,
        flow_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        session: Optional[Any] = None
    ) -> str:
        """
        Log security incident to file (no database storage)
        
        Returns incident ID for tracking
        """
        # Generate incident ID
        from uuid import uuid4
        incident_id = str(uuid4())
        
        # Log to security logger
        log_level = self._get_log_level(severity)
        self.logger.log(
            log_level,
            f"SECURITY INCIDENT [{severity.value}] {event_type.value}: "
            f"ID={incident_id}, User={user_email}, Flow={flow_id}, Details={details}"
        )
        
        return incident_id
    
    async def log_tampering_detected(
        self,
        flow_id: str,
        user_email: str,
        security_level: int,
        tamper_details: Dict[str, Any],
        session: Optional[Any] = None
    ):
        """Log email tampering detection (CRITICAL)"""
        details = {
            "security_level": security_level,
            "tamper_type": tamper_details.get("type", "signature_verification_failed"),
            "algorithm": tamper_details.get("algorithm"),
            "error": tamper_details.get("error"),
            "stack_trace": traceback.format_exc() if tamper_details.get("include_trace") else None
        }
        
        await self.log_security_incident(
            SecurityEventType.TAMPERING_DETECTED,
            Severity.CRITICAL,
            user_email=user_email,
            flow_id=flow_id,
            details=details,
            session=session
        )
        
        # Additional alerting for critical tampering
        self._send_critical_alert("EMAIL_TAMPERING", details)
    
    async def log_authentication_failed(
        self,
        user_email: Optional[str],
        auth_type: str,
        failure_reason: str,
        session: Optional[Any] = None
    ):
        """Log authentication failures"""
        details = {
            "auth_type": auth_type,  # "km_sae", "gmail_oauth", "certificate"
            "failure_reason": failure_reason,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.log_security_incident(
            SecurityEventType.AUTHENTICATION_FAILED,
            Severity.HIGH,
            user_email=user_email,
            details=details,
            session=session
        )
    
    async def log_key_security_issue(
        self,
        issue_type: str,
        flow_id: Optional[str] = None,
        user_email: Optional[str] = None,
        km_details: Optional[Dict[str, Any]] = None,
        session: Optional[Any] = None
    ):
        """Log quantum key security issues"""
        if issue_type == "insufficient_keys":
            event_type = SecurityEventType.INSUFFICIENT_KEYS
            severity = Severity.MEDIUM
        elif issue_type == "key_not_found":
            event_type = SecurityEventType.KEY_NOT_FOUND
            severity = Severity.HIGH
        elif issue_type == "low_entropy":
            event_type = SecurityEventType.LOW_ENTROPY_DETECTED
            severity = Severity.HIGH
        else:
            event_type = SecurityEventType.SUSPICIOUS_ACTIVITY
            severity = Severity.MEDIUM
        
        details = {
            "issue_type": issue_type,
            "km_details": km_details or {},
            "risk_assessment": self._assess_key_risk(issue_type, km_details)
        }
        
        await self.log_security_incident(
            event_type,
            severity,
            user_email=user_email,
            flow_id=flow_id,
            details=details,
            session=session
        )
    
    async def log_decryption_failure(
        self,
        flow_id: str,
        user_email: str,
        security_level: int,
        error_details: Dict[str, Any],
        session: Optional[Any] = None
    ):
        """Log decryption failures which may indicate attacks"""
        details = {
            "security_level": security_level,
            "error_type": error_details.get("type"),
            "error_message": error_details.get("message"),
            "algorithm": error_details.get("algorithm"),
            "possible_attack": self._analyze_decryption_failure(error_details)
        }
        
        # Higher severity if multiple failures for same user
        severity = await self._assess_failure_severity(user_email, session)
        
        await self.log_security_incident(
            SecurityEventType.DECRYPTION_FAILED,
            severity,
            user_email=user_email,
            flow_id=flow_id,
            details=details,
            session=session
        )
    
    async def log_suspicious_activity(
        self,
        activity_type: str,
        user_email: Optional[str] = None,
        activity_details: Optional[Dict[str, Any]] = None,
        session: Optional[Any] = None
    ):
        """Log suspicious user activity patterns"""
        details = {
            "activity_type": activity_type,
            "details": activity_details or {},
            "risk_score": self._calculate_risk_score(activity_type, activity_details),
            "recommended_action": self._get_recommended_action(activity_type)
        }
        
        await self.log_security_incident(
            SecurityEventType.SUSPICIOUS_ACTIVITY,
            Severity.MEDIUM,
            user_email=user_email,
            details=details,
            session=session
        )
    
    def _get_log_level(self, severity: Severity) -> int:
        """Convert severity to log level"""
        mapping = {
            Severity.LOW: logging.INFO,
            Severity.MEDIUM: logging.WARNING,
            Severity.HIGH: logging.ERROR,
            Severity.CRITICAL: logging.CRITICAL
        }
        return mapping.get(severity, logging.WARNING)
    
    def _send_critical_alert(self, alert_type: str, details: Dict[str, Any]):
        """Send critical security alerts (integrate with monitoring system)"""
        # In production, integrate with:
        # - Email alerts to security team
        # - SMS/phone alerts for critical incidents
        # - Security Information and Event Management (SIEM) systems
        # - Incident response automation
        
        alert_message = f"CRITICAL SECURITY ALERT: {alert_type}\nDetails: {json.dumps(details, indent=2)}"
        logger.critical(alert_message)
        
        # Placeholder for external alerting
        # await send_email_alert(security_team_email, alert_message)
        # await send_siem_event(alert_type, details)
    
    def _assess_key_risk(self, issue_type: str, km_details: Optional[Dict[str, Any]]) -> str:
        """Assess risk level of key-related security issues"""
        if issue_type == "low_entropy":
            return "HIGH - Possible QKD compromise or weak key generation"
        elif issue_type == "key_not_found":
            return "MEDIUM - Possible key synchronization issue or attack"
        elif issue_type == "insufficient_keys":
            return "LOW - Resource exhaustion, monitor for DoS patterns"
        else:
            return "UNKNOWN - Requires investigation"
    
    def _analyze_decryption_failure(self, error_details: Dict[str, Any]) -> str:
        """Analyze decryption failure patterns"""
        error_type = error_details.get("type", "")
        
        if "signature" in error_type.lower():
            return "TAMPERING - Message integrity compromised"
        elif "gcm" in error_type.lower() or "authentication" in error_type.lower():
            return "CORRUPTION - Data corrupted or attacked"
        elif "key" in error_type.lower():
            return "KEY_MISMATCH - Wrong keys or synchronization issue"
        else:
            return "UNKNOWN - Requires investigation"
    
    async def _assess_failure_severity(self, user_email: str, session: Optional[Any]) -> Severity:
        """Assess severity based on failure frequency"""
        # In production, query recent incidents for this user
        # If multiple failures in short time, escalate severity
        return Severity.MEDIUM  # Placeholder
    
    def _calculate_risk_score(self, activity_type: str, details: Optional[Dict[str, Any]]) -> int:
        """Calculate risk score for suspicious activities (0-100)"""
        base_scores = {
            "multiple_failed_logins": 60,
            "unusual_encryption_patterns": 40,
            "high_frequency_requests": 30,
            "off_hours_activity": 20,
            "unknown_device": 50
        }
        
        return base_scores.get(activity_type, 25)
    
    def _get_recommended_action(self, activity_type: str) -> str:
        """Get recommended response action"""
        actions = {
            "multiple_failed_logins": "Temporarily lock account, require MFA",
            "unusual_encryption_patterns": "Monitor closely, verify user identity",
            "high_frequency_requests": "Rate limit user, check for automation",
            "off_hours_activity": "Require additional authentication",
            "unknown_device": "Send device verification email"
        }
        
        return actions.get(activity_type, "Monitor and investigate")

# Global security auditor instance
security_auditor = SecurityAuditor()

# Convenience functions for common security events
async def log_tampering(flow_id: str, user_email: str, security_level: int, tamper_details: Dict[str, Any]):
    """Quick function to log tampering detection"""
    await security_auditor.log_tampering_detected(
        flow_id, user_email, security_level, tamper_details, None
    )

async def log_auth_failure(user_email: str, auth_type: str, reason: str):
    """Quick function to log authentication failures"""
    await security_auditor.log_authentication_failed(
        user_email, auth_type, reason, None
    )

async def log_key_issue(issue_type: str, **kwargs):
    """Quick function to log key security issues"""
    await security_auditor.log_key_security_issue(
        issue_type, session=None, **kwargs
    )
