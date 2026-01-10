from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.audit_log import AuditLog

class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        try:
            user = getattr(request.state, "user", None)
            async with AsyncSessionLocal() as session:
                log = AuditLog(
                    business_id=user.get("bid") if user else None,
                    user_id=user.get("sub") if user else None,
                    action="api_call",
                    path=str(request.url.path),
                    method=request.method,
                    ip=request.client.host if request.client else None,
                    details={"status_code": response.status_code},
                )
                session.add(log)
                await session.commit()
        except Exception:
            # Do not break response on audit failure
            pass
        return response
