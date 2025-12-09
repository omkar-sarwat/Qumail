import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from enum import Enum

logger = logging.getLogger(__name__)

class AuditEventType(Enum):
    EMAIL_ENCRYPTION_STARTED = "email_encryption_started"
    EMAIL_ENCRYPTION_COMPLETED = "email_encryption_completed"
    EMAIL_ENCRYPTION_FAILED = "email_encryption_failed"
    EMAIL_DECRYPTION_STARTED = "email_decryption_started"
    EMAIL_DECRYPTION_COMPLETED = "email_decryption_completed"
    EMAIL_DECRYPTION_FAILED = "email_decryption_failed"
    QUANTUM_KEY_REQUESTED = "quantum_key_requested"
    QUANTUM_KEY_CONSUMED = "quantum_key_consumed"
    UNAUTHORIZED_ACCESS_ATTEMPT = "unauthorized_access_attempt"
    SECURITY_VIOLATION = "security_violation"

class SecurityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AuditLogger:
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.audit")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - AUDIT - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    async def log_event(
    self, event_type: AuditEventType, user_id: Optional[int] = None,
    user_email: Optional[str] = None, email_id: Optional[str] = None,
        flow_id: Optional[str] = None, security_level: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None, severity: SecurityLevel = SecurityLevel.MEDIUM,
        db: Optional[AsyncSession] = None
    ) -> None:
        try:
            timestamp = datetime.utcnow()
            audit_entry = {
                "timestamp": timestamp.isoformat(),
                "event_type": event_type.value,
                "severity": severity.value,
                "user_id": user_id,
                "user_email": user_email,
                "email_id": email_id,
                "flow_id": flow_id,
                "security_level": security_level,
                "details": details or {},
                "source": "quantum_email_system"
            }
            
            log_message = self._format_audit_message(audit_entry)
            if severity == SecurityLevel.CRITICAL:
                self.logger.critical(log_message)
            elif severity == SecurityLevel.HIGH:
                self.logger.error(log_message)
            elif severity == SecurityLevel.MEDIUM:
                self.logger.warning(log_message)
            else:
                self.logger.info(log_message)
            
            if db is not None:
                await self._store_audit_log(audit_entry, db)
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
    
    def _format_audit_message(self, audit_entry: Dict[str, Any]) -> str:
        parts = [f"EVENT: {audit_entry['event_type']}", f"SEVERITY: {audit_entry['severity']}"]
        if audit_entry.get('user_email'):
            parts.append(f"USER: {audit_entry['user_email']}")
        if audit_entry.get('email_id'):
            parts.append(f"EMAIL_ID: {audit_entry['email_id']}")
        if audit_entry.get('flow_id'):
            parts.append(f"FLOW_ID: {audit_entry['flow_id']}")
        if audit_entry.get('security_level'):
            parts.append(f"SECURITY_LEVEL: {audit_entry['security_level']}")
        if audit_entry.get('details'):
            parts.append(f"DETAILS: {json.dumps(audit_entry['details'])}")
        return " | ".join(parts)
    
    async def _store_audit_log(self, audit_entry: Dict[str, Any], db: AsyncSession) -> None:
        """Store audit log entry in database - does NOT commit, leaves that to caller"""
        try:
            sqlite_create = """
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_type VARCHAR(100) NOT NULL,
                severity VARCHAR(20) NOT NULL,
                user_id INTEGER,
                user_email VARCHAR(255),
                email_id VARCHAR(64),
                flow_id VARCHAR(255),
                security_level INTEGER,
                details TEXT,
                source VARCHAR(100) NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """

            postgres_create = """
            CREATE TABLE IF NOT EXISTS audit_logs (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                event_type VARCHAR(100) NOT NULL,
                severity VARCHAR(20) NOT NULL,
                user_id INTEGER,
                user_email VARCHAR(255),
                email_id VARCHAR(64),
                flow_id VARCHAR(255),
                security_level INTEGER,
                details TEXT,
                source VARCHAR(100) NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
            """

            # Try to create table if it doesn't exist
            try:
                await db.execute(text(sqlite_create))
            except Exception:
                # Table might already exist or we need postgres syntax
                try:
                    await db.execute(text(postgres_create))
                except Exception as create_err:
                    logger.debug(f"Audit log table creation skipped (may already exist): {create_err}")

            # Insert audit entry
            insert_sql = """
            INSERT INTO audit_logs (timestamp, event_type, severity, user_id, user_email,
                                  email_id, flow_id, security_level, details, source)
            VALUES (:timestamp, :event_type, :severity, :user_id, :user_email,
                   :email_id, :flow_id, :security_level, :details, :source)
            """

            await db.execute(text(insert_sql), {
                "timestamp": audit_entry["timestamp"],
                "event_type": audit_entry["event_type"],
                "severity": audit_entry["severity"],
                "user_id": audit_entry["user_id"],
                "user_email": audit_entry["user_email"],
                "email_id": audit_entry["email_id"],
                "flow_id": audit_entry["flow_id"],
                "security_level": audit_entry["security_level"],
                "details": json.dumps(audit_entry["details"]),
                "source": audit_entry["source"]
            })
            
            # Flush to write to DB but don't commit (let the caller handle transaction)
            await db.flush()
            
        except Exception as e:
            logger.error(f"Failed to store audit log: {e}")
            # Don't rollback - let the caller handle transaction management

    async def log_encryption_started(self, user_id: int, user_email: str, recipient_email: str,
                                   security_level: int, flow_id: str, db: Optional[AsyncSession] = None):
        await self.log_event(AuditEventType.EMAIL_ENCRYPTION_STARTED, user_id=user_id,
                           user_email=user_email, flow_id=flow_id, security_level=security_level,
                           details={"recipient_email": recipient_email}, severity=SecurityLevel.MEDIUM, db=db)

    async def log_encryption_completed(self, user_id: int, user_email: str, email_id: str,
                                     flow_id: str, security_level: int, algorithm: str,
                                     quantum_enhanced: bool, db: Optional[AsyncSession] = None):
        await self.log_event(AuditEventType.EMAIL_ENCRYPTION_COMPLETED, user_id=user_id,
                           user_email=user_email, email_id=email_id, flow_id=flow_id,
                           security_level=security_level, details={"algorithm": algorithm,
                           "quantum_enhanced": quantum_enhanced}, severity=SecurityLevel.LOW, db=db)

    async def log_decryption_started(self, user_id: int, user_email: str, email_id: str,
                                   flow_id: str, security_level: int, db: Optional[AsyncSession] = None):
        await self.log_event(AuditEventType.EMAIL_DECRYPTION_STARTED, user_id=user_id,
                           user_email=user_email, email_id=email_id, flow_id=flow_id,
                           security_level=security_level, severity=SecurityLevel.MEDIUM, db=db)

    async def log_unauthorized_access(self, user_email: str, email_id: str,
                                    attempted_operation: str, db: Optional[AsyncSession] = None):
        await self.log_event(AuditEventType.UNAUTHORIZED_ACCESS_ATTEMPT, user_email=user_email,
                           email_id=email_id, details={"attempted_operation": attempted_operation,
                           "blocked": True}, severity=SecurityLevel.HIGH, db=db)

audit_logger = AuditLogger()
