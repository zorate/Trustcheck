import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status

from app.core.security import hash_password
from app.models.business import Business
from app.models.business_user import BusinessUser
from app.schemas.business import BusinessOut, CreateStaffRequest, StaffOut, UpdateStaffRequest
from app.services.audit_service import write_audit

logger = logging.getLogger(__name__)


async def get_business_profile(business_id: str) -> BusinessOut:
    biz = await Business.get(business_id)
    if not biz or biz.deleted_at:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")
    return BusinessOut(id=biz.id, name=biz.name, email=biz.email, phone=biz.phone,
                       address=biz.address, business_type=biz.business_type,
                       is_active=biz.is_active, created_at=biz.created_at)


async def create_staff(req: CreateStaffRequest, business_id: str,
                       actor_id: str, ip: Optional[str] = None) -> StaffOut:
    existing = await BusinessUser.find_one(BusinessUser.email == req.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="An account with this email already exists")

    user = BusinessUser(business_id=business_id, email=req.email, full_name=req.full_name,
                        hashed_password=hash_password(req.password), role=req.role)
    await user.insert()
    await write_audit(action="business_user.create", business_id=business_id,
                      actor_id=actor_id, resource_type="business_user",
                      resource_id=user.id, detail={"role": req.role}, ip_address=ip)
    return _staff_out(user)


async def list_staff(business_id: str) -> list[StaffOut]:
    users = await BusinessUser.find(
        BusinessUser.business_id == business_id,
        BusinessUser.deleted_at == None,  # noqa: E711
    ).to_list()
    return [_staff_out(u) for u in users]


async def update_staff(staff_id: str, req: UpdateStaffRequest, business_id: str,
                       actor_id: str, actor_role: str, ip: Optional[str] = None) -> StaffOut:
    user = await _get_staff_scoped(staff_id, business_id)

    if user.role == "owner" and actor_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Owner account can only be modified by the owner")
    if req.full_name is not None:
        user.full_name = req.full_name
    if req.role is not None:
        if req.role == "owner":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Cannot assign owner role via staff update")
        user.role = req.role
    if req.is_active is not None:
        user.is_active = req.is_active

    user.updated_at = datetime.now(timezone.utc)
    await user.save()
    await write_audit(action="business_user.update", business_id=business_id,
                      actor_id=actor_id, resource_type="business_user",
                      resource_id=staff_id, ip_address=ip)
    return _staff_out(user)


async def deactivate_staff(staff_id: str, business_id: str,
                           actor_id: str, ip: Optional[str] = None) -> None:
    user = await _get_staff_scoped(staff_id, business_id)
    if user.role == "owner":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Cannot deactivate the business owner account")
    now = datetime.now(timezone.utc)
    user.is_active = False
    user.deleted_at = now
    user.updated_at = now
    await user.save()
    await write_audit(action="business_user.deactivate", business_id=business_id,
                      actor_id=actor_id, resource_type="business_user",
                      resource_id=staff_id, ip_address=ip)


async def _get_staff_scoped(staff_id: str, business_id: str) -> BusinessUser:
    user = await BusinessUser.find_one(
        BusinessUser.id == staff_id,
        BusinessUser.business_id == business_id,
        BusinessUser.deleted_at == None,  # noqa: E711
    )
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Staff member not found")
    return user


def _staff_out(u: BusinessUser) -> StaffOut:
    return StaffOut(id=u.id, business_id=u.business_id, email=u.email,
                    full_name=u.full_name, role=u.role, is_active=u.is_active,
                    created_at=u.created_at)