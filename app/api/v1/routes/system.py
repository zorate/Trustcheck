from typing import Optional
from fastapi import APIRouter, Depends, Query
from app.api.deps import CurrentUser, require_role
from app.core.config import get_settings
from app.core.database import ping_db
from app.models.audit_log import AuditLog
from app.schemas.common import APIResponse
from app.schemas.score import AuditLogOut

router = APIRouter(tags=["System"])
settings = get_settings()


@router.get("/health", response_model=APIResponse[dict])
async def health_check():
    db_ok = await ping_db()
    return APIResponse(
        success=True,
        data={"status": "ok" if db_ok else "degraded",
              "database": "connected" if db_ok else "unreachable",
              "version": settings.APP_VERSION,
              "environment": settings.ENVIRONMENT},
    )


@router.get("/audit-logs", response_model=APIResponse[list[AuditLogOut]])
async def get_audit_logs(page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200),
                         action: Optional[str] = Query(None),
                         current_user: CurrentUser = Depends(require_role("owner"))):
    skip = (page - 1) * page_size
    filters = [AuditLog.business_id == current_user.business_id]
    if action:
        filters.append(AuditLog.action == action)
    query = AuditLog.find(*filters)
    total = await query.count()
    logs = await query.sort(-AuditLog.created_at).skip(skip).limit(page_size).to_list()
    return APIResponse(
        success=True,
        data=[AuditLogOut(id=log.id, business_id=log.business_id, actor_id=log.actor_id,
                          action=log.action, resource_type=log.resource_type,
                          resource_id=log.resource_id, ip_address=log.ip_address,
                          created_at=log.created_at) for log in logs],
        meta={"total": total, "page": page, "page_size": page_size, "has_more": (page * page_size) < total},
    )
