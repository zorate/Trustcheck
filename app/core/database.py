import logging
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Module-level client — created once on startup
_client: AsyncIOMotorClient | None = None


async def connect_db() -> None:
    """Initialize MongoDB connection and Beanie ODM."""
    global _client

    settings = get_settings()

    # Import all document models here to register them with Beanie
    from app.models.business import Business
    from app.models.business_user import BusinessUser
    from app.models.person import Person
    from app.models.relationship import Relationship
    from app.models.payment_record import PaymentRecord
    from app.models.trust_score import TrustScore
    from app.models.reference import Reference
    from app.models.audit_log import AuditLog

    _client = AsyncIOMotorClient(
        settings.MONGODB_URL,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=10000,
        socketTimeoutMS=30000,
    )

    await init_beanie(
        database=_client[settings.MONGODB_DB_NAME],
        document_models=[
            Business,
            BusinessUser,
            Person,
            Relationship,
            PaymentRecord,
            TrustScore,
            Reference,
            AuditLog,
        ],
    )

    logger.info("MongoDB connected — database: %s", settings.MONGODB_DB_NAME)


async def close_db() -> None:
    """Close MongoDB connection on shutdown."""
    global _client
    if _client:
        _client.close()
        logger.info("MongoDB connection closed")


async def ping_db() -> bool:
    """Health check — returns True if MongoDB is reachable."""
    global _client
    if not _client:
        return False
    try:
        await _client.admin.command("ping")
        return True
    except Exception:
        return False