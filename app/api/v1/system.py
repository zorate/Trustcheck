from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.rate_limit import rate_limit
from app.middleware.auth import get_current_user
from app.services.rbac import ensure_admin
from app.models.audit_log import AuditLog
from app.schemas.audit_log import AuditLogResponse

router = APIRouter(prefix="/api/v1/system", tags=["system"])

@router.get("/health")
async def health():
    return {"status": "ok"}

@router.get("/audit", response_model=list[AuditLogResponse])
async def audit_logs(request: Request, db: AsyncSession = Depends(get_db)):
    rate_limit(request)
    user = await get_current_user(request)
    ensure_admin(user)
    q = select(AuditLog).where(AuditLog.business_id == user["bid"], AuditLog.deleted == False).order_by(AuditLog.created_at.desc()).limit(200)
    logs = (await db.execute(q)).scalars().all()
    return [
        AuditLogResponse(
            id=l.id,
            business_id=l.business_id,
            user_id=l.user_id,
            action=l.action,
            path=l.path,
            method=l.method,
            ip=l.ip,
            created_at=l.created_at,
            details=l.details,
        ) for l in logs
    ]
