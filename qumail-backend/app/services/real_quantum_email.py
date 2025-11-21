"""Mongo-backed helper for quantum email specific views."""

import json
import logging
from typing import Any, Dict, List, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from ..mongo_models import EmailDirection
from ..mongo_repositories import EmailRepository

logger = logging.getLogger(__name__)


class RealQuantumEmailService:
    """Provides read helpers for quantum-tagged emails stored in MongoDB."""

    def __init__(self, max_results: int = 100):
        self.max_results = max_results

    async def get_emails(
        self,
        user_email: str,
        folder: str,
        db: AsyncIOMotorDatabase,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Return quantum emails for the given folder without decrypting bodies."""

        if db is None:
            raise ValueError("Database dependency is required")

        repo = EmailRepository(db)
        direction_map = {
            "inbox": EmailDirection.RECEIVED,
            "sent": EmailDirection.SENT,
        }
        direction = direction_map.get(folder.lower())
        docs = await repo.list_by_user(
            user_email,
            direction=direction,
            limit=limit or self.max_results,
        )

        quantum_levels = {1, 2, 3, 4}
        response: List[Dict[str, Any]] = []

        for email in docs:
            if email.security_level not in quantum_levels:
                continue

            metadata = email.encryption_metadata or {}
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except json.JSONDecodeError:
                    metadata = {"raw_metadata": metadata}

            snippet = metadata.get("snippet") or ""
            if not snippet and email.body_encrypted:
                snippet = (
                    f"{email.body_encrypted[:160]}..."
                    if len(email.body_encrypted) > 160
                    else email.body_encrypted
                )

            response.append(
                {
                    "id": email.flow_id,
                    "flow_id": email.flow_id,
                    "from": email.sender_email,
                    "to": email.receiver_email,
                    "subject": email.subject,
                    "snippet": snippet,
                    "timestamp": email.timestamp.isoformat(),
                    "read": email.is_read,
                    "security_level": email.security_level,
                    "encrypted": True,
                    "source": metadata.get("source", "qumail"),
                    "labels": metadata.get("labels", []),
                    "gmailMessageId": email.gmail_message_id,
                    "hasAttachments": metadata.get("hasAttachments", False),
                    "senderDisplay": metadata.get("senderDisplay", email.sender_email),
                    "receiverDisplay": metadata.get("receiverDisplay", email.receiver_email),
                }
            )

        logger.info(
            "Quantum folder %s returned %d messages for %s",
            folder,
            len(response),
            user_email,
        )
        return response

    async def mark_as_read(
        self,
        email_id: str,
        user_email: str,
        db: AsyncIOMotorDatabase,
    ) -> bool:
        """Mark a stored quantum email as read (id or flow_id)."""

        if db is None:
            raise ValueError("Database dependency is required")

        repo = EmailRepository(db)
        normalized = email_id.replace("quantum_", "", 1) if email_id.startswith("quantum_") else email_id
        email = await repo.find_by_id(normalized)
        if not email:
            email = await repo.find_by_flow_id(normalized)

        if not email:
            raise ValueError(f"Email {normalized} not found")

        if (
            email.sender_email != user_email
            and email.receiver_email != user_email
        ):
            raise PermissionError("Access denied for this email")

        updated = await repo.mark_as_read(email.id)
        logger.info("Quantum email %s marked read for %s", normalized, user_email)
        return updated


# Shared instance
real_quantum_email_service = RealQuantumEmailService()
