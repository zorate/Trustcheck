from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.rate_limit import rate_limit
from app.schemas.business import StaffResponse
from app.models.user import BusinessUser
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/api/v1/users", tags=["users"])

@router.get("/", response_model=list[StaffResponse])
async def list_staff(request: Request, db: AsyncSession = Depends(get_db)):
    rate_limit(request)
    user = await get_current_user(request)
    q = select(BusinessUser).where(BusinessUser.business_id == user["bid"], BusinessUser.deleted == False)
    users = (await db.execute(q)).scalars().all()
    return [StaffResponse(id=u.id, full_name=u.full_name, email=u.email, phone=u.phone, is_admin=u.is_admin, is_active=u.is_active) for u in users]
