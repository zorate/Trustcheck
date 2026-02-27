import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from jose import JWTError

from app.core.config import get_settings
from app.core.security import (
    create_access_token, create_refresh_token, decode_refresh_token,
    hash_password, verify_password,
)
from app.models.business import Business
from app.models.business_user import BusinessUser
from app.schemas.auth import (
    AuthResponse, BusinessRegisterRequest, BusinessUserOut,
    LoginRequest, TokenResponse,
)
from app.services.audit_service import write_audit

logger = logging.getLogger(__name__)
settings = get_settings()


async def register_business(req: BusinessRegisterRequest, ip: Optional[str] = None) -> AuthResponse:
    existing = await BusinessUser.find_one(BusinessUser.email == req.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="An account with this email already exists")

    biz_email_taken = await Business.find_one(Business.email == req.email)
    if biz_email_taken:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="An account with this email already exists")

    business = Business(name=req.business_name, email=req.email,
                        phone=req.phone, business_type=req.business_type)
    await business.insert()

    owner = BusinessUser(business_id=business.id, email=req.email,
                         full_name=req.full_name,
                         hashed_password=hash_password(req.password), role="owner")
    await owner.insert()

    await write_audit(action="business.register", business_id=business.id,
                      actor_id=owner.id, resource_type="business",
                      resource_id=business.id,
                      detail={"business_type": req.business_type}, ip_address=ip)

    return AuthResponse(user=_user_out(owner), tokens=_build_tokens(owner))


async def login(req: LoginRequest, ip: Optional[str] = None) -> AuthResponse:
    user = await BusinessUser.find_one(BusinessUser.email == req.email)
    dummy_hash = "$2b$12$notavalidhashbutconstanttimePADDINGXXXXXXXXXXXXXXXXXXXX"
    hashed = user.hashed_password if user else dummy_hash
    valid = verify_password(req.password, hashed)

    if not user or not valid or not user.is_active or user.deleted_at is not None:
        await write_audit(action="business_user.login_failed",
                          detail={"email_domain": req.email.split("@")[-1]}, ip_address=ip)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid credentials")

    user.last_login_at = datetime.now(timezone.utc)
    await user.save()
    await write_audit(action="business_user.login", business_id=user.business_id,
                      actor_id=user.id, ip_address=ip)
    return AuthResponse(user=_user_out(user), tokens=_build_tokens(user))


async def refresh_tokens(refresh_token: str, ip: Optional[str] = None) -> TokenResponse:
    try:
        payload = decode_refresh_token(refresh_token)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid or expired refresh token")

    user = await BusinessUser.get(payload.get("sub"))
    if not user or not user.is_active or user.deleted_at:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="User account is inactive")

    await write_audit(action="business_user.token_refresh", business_id=user.business_id,
                      actor_id=user.id, ip_address=ip)
    return _build_tokens(user)


def _build_tokens(user: BusinessUser) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(user.id, user.business_id, user.role),
        refresh_token=create_refresh_token(user.id, user.business_id),
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


def _user_out(user: BusinessUser) -> BusinessUserOut:
    return BusinessUserOut(id=user.id, business_id=user.business_id, email=user.email,
                           full_name=user.full_name, role=user.role, is_active=user.is_active)