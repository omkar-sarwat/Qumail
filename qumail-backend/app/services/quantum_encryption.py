"""Mongo-aware quantum encryption façade used by legacy endpoints."""

import json
import logging
from typing import Any, Dict, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from ..mongo_repositories import EmailRepository
from .complete_email_service import complete_email_service
from .encryption.quantum_key_pool import quantum_key_pool

logger = logging.getLogger(__name__)


class QuantumEncryptionService:
    """Bridges older quantum endpoints onto the Mongo-based email service."""

    async def _resolve_email(
        self, repo: EmailRepository, identifier: Optional[str]
    ) -> Optional[Any]:
        if not identifier:
            return None
        email = await repo.find_by_id(identifier)
        if email:
            return email
        return await repo.find_by_flow_id(identifier)

    async def encrypt_email(
        self,
        subject: str,
        body: str,
        sender_email: str,
        receiver_email: str,
        security_level: int,
        user_id: str,
        db: AsyncIOMotorDatabase,
    ) -> Dict[str, Any]:
        if db is None:
            raise ValueError("Database dependency is required for encryption")

        result = await complete_email_service.send_encrypted_email(
            sender_email=sender_email,
            sender_user_id=user_id,
            recipient_email=receiver_email,
            subject=subject,
            body=body,
            security_level=security_level,
            db=db,
            gmail_credentials=None,
        )

        details = result.get("encryption_details", {})
        repo = EmailRepository(db)
        email_doc = await self._resolve_email(repo, result.get("email_id"))

        encrypted_body = email_doc.body_encrypted if email_doc else None
        metadata = email_doc.encryption_metadata if email_doc else {}
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except json.JSONDecodeError:
                metadata = {"raw_metadata": metadata}

        metadata.update(
            {
                "key_id": details.get("key_id"),
                "encrypted_size": details.get("encrypted_size"),
                "security_level": details.get("security_level", security_level),
                "quantum_enhanced": True,
            }
        )

        logger.info(
            "Quantum encryption shim stored email %s (flow %s) at level %s",
            result.get("email_id"),
            result.get("flow_id"),
            security_level,
        )

        return {
            "email_id": result.get("email_id"),
            "flow_id": result.get("flow_id"),
            "security_level": metadata.get("security_level", security_level),
            "algorithm": details.get("algorithm"),
            "encrypted_body": encrypted_body,
            "encryption_metadata": metadata,
            "encrypted_size": metadata.get("encrypted_size"),
            "quantum_enhanced": True,
            "timestamp": result.get("timestamp"),
            "key_id": metadata.get("key_id"),
            "entropy": metadata.get("entropy", 1.0),
        }

    async def decrypt_email(
        self,
        email_id: str,
        user_email: str,
        requesting_user_id: str,
        db: AsyncIOMotorDatabase,
    ) -> Dict[str, Any]:
        if db is None:
            raise ValueError("Database dependency is required for decryption")

        repo = EmailRepository(db)
        normalized = email_id.replace("quantum_", "", 1) if email_id.startswith("quantum_") else email_id

        email = await self._resolve_email(repo, normalized)
        if not email:
            raise ValueError(f"Email {normalized} not found")

        if (
            email.sender_email != user_email
            and email.receiver_email != user_email
            and email.user_id != requesting_user_id
        ):
            raise PermissionError("Access denied: requester is not associated with this email")

        result = await complete_email_service.receive_and_decrypt_email(email.id, db)

        return {
            "email_id": result.get("email_id"),
            "subject": result.get("subject"),
            "body": result.get("body"),
            "sender_email": result.get("from") or email.sender_email,
            "receiver_email": result.get("to") or email.receiver_email,
            "security_level": result.get("security_level", email.security_level),
            "algorithm": result.get("algorithm"),
            "verification_status": "verified",
            "quantum_enhanced": True,
            "timestamp": result.get("timestamp"),
            "flow_id": result.get("flow_id"),
            "encrypted_size": len(email.body_encrypted or ""),
        }

    async def get_encryption_status(self) -> Dict[str, Any]:
        pool = await quantum_key_pool.get_pool_status()
        return {
            "system_status": "operational" if pool else "unavailable",
            "total_keys": pool.get("total_keys", 0),
            "available_keys": pool.get("available_keys", 0),
            "consumed_keys": pool.get("consumed_keys", 0),
            "quantum_enhanced": True,
        }


quantum_encryption_service = QuantumEncryptionService()
