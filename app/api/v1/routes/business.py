from fastapi import APIRouter, Depends, Request
from app.api.deps import CurrentUser, get_client_ip, get_current_user, require_role
from app.schemas.business import BusinessOut, CreateStaffRequest, StaffOut, UpdateStaffRequest
from app.schemas.common import APIResponse
from app.services import business_service

router = APIRouter(prefix="/business", tags=["Business"])


@router.get("/profile", response_model=APIResponse[BusinessOut])
async def get_profile(current_user: CurrentUser = Depends(get_current_user)):
    return APIResponse(data=await business_service.get_business_profile(current_user.business_id))


@router.get("/staff", response_model=APIResponse[list[StaffOut]])
async def list_staff(current_user: CurrentUser = Depends(require_role("admin"))):
    return APIResponse(data=await business_service.list_staff(current_user.business_id))


@router.post("/staff", response_model=APIResponse[StaffOut], status_code=201)
async def create_staff(body: CreateStaffRequest, request: Request,
                       current_user: CurrentUser = Depends(require_role("owner")),
                       ip: str | None = Depends(get_client_ip)):
    staff = await business_service.create_staff(body, current_user.business_id,
                                                current_user.user_id, ip=ip)
    return APIResponse(data=staff, message="Staff member created")


@router.patch("/staff/{staff_id}", response_model=APIResponse[StaffOut])
async def update_staff(staff_id: str, body: UpdateStaffRequest, request: Request,
                       current_user: CurrentUser = Depends(require_role("admin")),
                       ip: str | None = Depends(get_client_ip)):
    staff = await business_service.update_staff(staff_id, body, current_user.business_id,
                                                current_user.user_id, current_user.role, ip=ip)
    return APIResponse(data=staff)


@router.delete("/staff/{staff_id}", response_model=APIResponse[None])
async def deactivate_staff(staff_id: str, request: Request,
                           current_user: CurrentUser = Depends(require_role("owner")),
                           ip: str | None = Depends(get_client_ip)):
    await business_service.deactivate_staff(staff_id, current_user.business_id,
                                            current_user.user_id, ip=ip)
    return APIResponse(message="Staff member deactivated")