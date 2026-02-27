import logging
from typing import Any, Optional
from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


async def write_audit(
    action: str,
    business_id: Optional[str] = None,
    actor_id: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    detail: Optional[dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> None:
    try:
        log = AuditLog(
            business_id=business_id,
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            detail=detail,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await log.insert()
    except Exception as exc:
        logger.error("Audit write failed for action=%s: %s", action, exc)