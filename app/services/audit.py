from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog

async def audit(session: AsyncSession, business_id, user_id, action: str, details: dict | None = None):
    log = AuditLog(
        business_id=business_id,
        user_id=user_id,
        action=action,
        path="",
        method="",
        ip=None,
        details=details or {},
    )
    session.add(log)
