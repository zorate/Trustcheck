from fastapi import APIRouter, Depends, Request
from app.api.deps import get_client_ip
from app.schemas.auth import AuthResponse, BusinessRegisterRequest, LoginRequest, RefreshRequest, TokenResponse
from app.schemas.common import APIResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=APIResponse[AuthResponse], status_code=201)
async def register(body: BusinessRegisterRequest, request: Request,
                   ip: str | None = Depends(get_client_ip)):
    result = await auth_service.register_business(body, ip=ip)
    return APIResponse(data=result, message="Business registered successfully")


@router.post("/login", response_model=APIResponse[AuthResponse])
async def login(body: LoginRequest, request: Request,
                ip: str | None = Depends(get_client_ip)):
    result = await auth_service.login(body, ip=ip)
    return APIResponse(data=result)


@router.post("/refresh", response_model=APIResponse[TokenResponse])
async def refresh(body: RefreshRequest, request: Request,
                  ip: str | None = Depends(get_client_ip)):
    tokens = await auth_service.refresh_tokens(body.refresh_token, ip=ip)
    return APIResponse(data=tokens)