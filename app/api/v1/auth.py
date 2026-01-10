from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import create_access_token, create_refresh_token, verify_password, hash_password, decode_token
from app.core.rate_limit import rate_limit
from app.schemas.auth import RegisterBusinessRequest, TokenResponse, LoginRequest, RefreshRequest, MeResponse
from app.models.business import Business
from app.models.user import BusinessUser

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

@router.post("/register", response_model=TokenResponse)
async def register_business(payload: RegisterBusinessRequest, request: Request, db: AsyncSession = Depends(get_db)):
    rate_limit(request)
    # Create business
    business = Business(name=payload.name, country=payload.country, phone=payload.phone, email=payload.email)
    db.add(business)
    await db.flush()
    # Create admin user
    admin = BusinessUser(
        business_id=business.id,
        email=payload.admin_email,
        full_name=payload.admin_full_name,
        password_hash=hash_password(payload.admin_password),
        is_admin=True,
        is_active=True,
    )
    db.add(admin)
    await db.commit()
    scopes = ["admin", "staff"]
    return TokenResponse(
        access_token=create_access_token(str(admin.id), str(business.id), scopes),
        refresh_token=create_refresh_token(str(admin.id), str(business.id), scopes),
    )

@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    rate_limit(request)
    q = select(BusinessUser).where(BusinessUser.email == payload.email, BusinessUser.deleted == False)
    user = (await db.execute(q)).scalars().first()
    if not user or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    scopes = ["admin", "staff"] if user.is_admin else ["staff"]
    return TokenResponse(
        access_token=create_access_token(str(user.id), str(user.business_id), scopes),
        refresh_token=create_refresh_token(str(user.id), str(user.business_id), scopes),
    )

@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest, request: Request):
    rate_limit(request)
    try:
        data = decode_token(payload.refresh_token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    if data.get("typ") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
    scopes = data.get("scp", [])
    return TokenResponse(
        access_token=create_access_token(data["sub"], data.get("bid"), scopes),
        refresh_token=create_refresh_token(data["sub"], data.get("bid"), scopes),
    )

@router.get("/me", response_model=MeResponse)
async def me(request: Request, db: AsyncSession = Depends(get_db)):
    rate_limit(request)
    from app.middleware.auth import get_current_user
    user_payload = await get_current_user(request)
    q = select(BusinessUser).where(BusinessUser.id == user_payload["sub"], BusinessUser.deleted == False)
    user = (await db.execute(q)).scalars().first()
    return MeResponse(
        id=user.id,
        business_id=user.business_id,
        email=user.email,
        full_name=user.full_name,
        is_admin=user.is_admin,
    )
