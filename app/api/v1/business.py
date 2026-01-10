from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.rate_limit import rate_limit
from app.schemas.business import BusinessResponse, CreateStaffRequest, StaffResponse
from app.models.business import Business
from app.models.user import BusinessUser
from app.core.security import hash_password
from app.middleware.auth import get_current_user
from app.services.rbac import ensure_admin

router = APIRouter(prefix="/api/v1/business", tags=["business"])

@router.get("/profile", response_model=BusinessResponse)
async def profile(request: Request, db: AsyncSession = Depends(get_db)):
    rate_limit(request)
    user = await get_current_user(request)
    q = select(Business).where(Business.id == user["bid"], Business.deleted == False)
    business = (await db.execute(q)).scalars().first()
    return BusinessResponse(id=business.id, name=business.name, country=business.country, phone=business.phone, email=business.email)

@router.post("/staff", response_model=StaffResponse)
async def create_staff(payload: CreateStaffRequest, request: Request, db: AsyncSession = Depends(get_db)):
    rate_limit(request)
    user = await get_current_user(request)
    ensure_admin(user)
    staff = BusinessUser(
        business_id=user["bid"],
        email=payload.email,
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        phone=payload.phone,
        is_admin=payload.is_admin,
        is_active=True,
    )
    db.add(staff)
    await db.commit()
    return StaffResponse(id=staff.id, full_name=staff.full_name, email=staff.email, phone=staff.phone, is_admin=staff.is_admin, is_active=staff.is_active)
