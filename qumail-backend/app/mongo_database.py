"""MongoDB database configuration and connection management."""

import logging
from typing import Any, Optional, Tuple

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class MongoDB:
    client: Optional[Any] = None
    db: Optional[Any] = None

mongodb = MongoDB()

def _extract_db_name(connection_url: str) -> str:
    parts = connection_url.rsplit('/', 1)
    if len(parts) == 1:
        return "admin"
    db_segment = parts[-1].split('?')[0]
    return db_segment or "admin"


def _build_motor_kwargs(connection_url: str) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "maxPoolSize": settings.mongo_max_pool_size,
        "minPoolSize": settings.mongo_min_pool_size,
        "serverSelectionTimeoutMS": settings.mongo_connection_timeout_ms,
    }

    if settings.mongo_tls_allow_invalid_certs:
        kwargs["tlsAllowInvalidCertificates"] = True
        kwargs["tlsAllowInvalidHostnames"] = True

    if settings.mongo_tls_ca_file:
        kwargs["tlsCAFile"] = settings.mongo_tls_ca_file
    elif connection_url.startswith("mongodb+srv://"):
        try:  # Prefer certifi CA bundle for SRV URLs on Windows dev setups
            import certifi  # type: ignore

            kwargs["tlsCAFile"] = certifi.where()
        except Exception:  # pragma: no cover - optional dependency failures
            pass

    if settings.mongo_force_local and connection_url.startswith("mongodb://"):
        kwargs.setdefault("directConnection", True)

    return kwargs


async def _attempt_connection(connection_url: str) -> Tuple[AsyncIOMotorClient, AsyncIOMotorDatabase, str]:
    client = AsyncIOMotorClient(
        connection_url,
        **_build_motor_kwargs(connection_url),
    )
    db_name = _extract_db_name(connection_url)
    database = client[db_name]
    await client.admin.command('ping')
    return client, database, db_name


async def connect_to_mongo():
    """Create database connection with fallback support."""
    attempts = []
    candidates = []

    primary_url = settings.database_url.strip()
    if primary_url and not settings.mongo_force_local:
        candidates.append(("primary", primary_url))

    fallback_url = settings.fallback_database_url.strip()
    if fallback_url and fallback_url != primary_url:
        candidates.append(("fallback", fallback_url))

    last_error: Optional[Exception] = None

    for label, url in candidates:
        try:
            client, database, db_name = await _attempt_connection(url)
            if mongodb.client:
                mongodb.client.close()
            mongodb.client = client
            mongodb.db = database
            logger.info("Connected to MongoDB database '%s' using %s url", db_name, label)
            return
        except Exception as exc:  # pragma: no cover - network specific
            attempts.append(f"{label}: {exc}")
            logger.warning("MongoDB %s connection failed: %s", label, exc)
            last_error = exc

    error_details = '; '.join(attempts) or 'no connection attempts were made'

    if settings.mongo_embedded_enabled:
        if _start_embedded_database(error_details):
            return

    raise RuntimeError(f"Unable to connect to MongoDB ({error_details})") from last_error

async def close_mongo_connection():
    """Close database connection."""
    if mongodb.client:
        mongodb.client.close()
        logger.info("MongoDB connection closed")

def get_database() -> AsyncIOMotorDatabase:
    """Get database instance for dependency injection."""
    if mongodb.db is None:
        raise RuntimeError("Database not initialized. Call connect_to_mongo() first.")
    return mongodb.db

async def init_collections():
    """Initialize MongoDB collections and indexes."""
    db = get_database()
    
    # Users collection indexes
    # Try unique index (MongoDB), fallback for Mongita
    try:
        await db.users.create_index("email", unique=True)
    except Exception:
        await db.users.create_index("email")
    await db.users.create_index("created_at")
    
    # Emails collection indexes
    await db.emails.create_index("flow_id", unique=True)
    await db.emails.create_index("user_id")
    await db.emails.create_index("sender_email")
    await db.emails.create_index("receiver_email")
    await db.emails.create_index("gmail_message_id")
    await db.emails.create_index("security_level")
    await db.emails.create_index("direction")
    await db.emails.create_index("is_read")
    await db.emails.create_index("timestamp")
    await db.emails.create_index([("user_id", 1), ("timestamp", -1)])
    
    # Drafts collection indexes
    await db.drafts.create_index("user_id")
    await db.drafts.create_index("user_email")  # For cross-device sync via Google account
    await db.drafts.create_index("created_at")
    await db.drafts.create_index([("user_email", 1), ("updated_at", -1)])  # Optimized query for listing
    
    # Encryption metadata collection indexes
    await db.encryption_metadata.create_index("flow_id", unique=True)
    await db.encryption_metadata.create_index("email_id")
    await db.encryption_metadata.create_index("key_id")
    
    # Key usage collection indexes
    await db.key_usage.create_index("email_id")
    await db.key_usage.create_index("key_id")
    await db.key_usage.create_index("timestamp")
    
    # Attachments collection indexes
    await db.attachments.create_index("email_id")
    
    logger.info("✅ MongoDB collections and indexes initialized")


def _start_embedded_database(error_details: str) -> bool:
    """Start an embedded MongoDB-compatible store when remote connections fail."""
    try:
        from .mongo_memory_client import create_async_memory_client
    except Exception as import_error:  # pragma: no cover - optional dependency issues
        logger.error(
            "Embedded MongoDB fallback unavailable (missing dependency): %s",
            import_error,
        )
        return False

    try:
        client, database = create_async_memory_client(settings.mongo_embedded_db_name)
        if mongodb.client:
            mongodb.client.close()
        mongodb.client = client
        mongodb.db = database
        logger.warning(
            "Using embedded MongoDB database '%s' (reason: %s)",
            settings.mongo_embedded_db_name,
            error_details,
        )
        return True
    except Exception as exc:  # pragma: no cover - unexpected failure path
        logger.error("Failed to initialize embedded MongoDB fallback: %s", exc)
        return False
