from typing import Optional

from fastapi import APIRouter, Depends, Query, Request

from app.api.deps import CurrentUser, get_client_ip, get_current_user, require_role
from app.schemas.common import APIResponse
from app.schemas.person import AddPersonRequest, PersonOut, UpdatePersonRequest
from app.services import person_service

router = APIRouter(prefix="/persons", tags=["Persons"])


@router.post("", response_model=APIResponse[PersonOut], status_code=201)
async def add_person(
    body: AddPersonRequest,
    request: Request,
    current_user: CurrentUser = Depends(require_role("staff")),
    ip: Optional[str] = Depends(get_client_ip),
):
    person = await person_service.add_person(
        body, current_user.business_id, current_user.user_id, ip=ip
    )
    return APIResponse(success=True, data=person)


@router.get("", response_model=APIResponse[list[PersonOut]])
async def list_persons(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
):
    persons, total = await person_service.list_persons(
        current_user.business_id, page=page, page_size=page_size
    )
    return APIResponse(
        success=True,
        data=persons,
        meta={
            "total": total,
            "page": page,
            "page_size": page_size,
            "has_more": (page * page_size) < total,
        },
    )


@router.get("/lookup", response_model=APIResponse[PersonOut])
async def lookup_by_phone(
    phone: str = Query(..., description="Phone number in any format"),
    current_user: CurrentUser = Depends(get_current_user),
):
    person = await person_service.get_person_by_phone(phone, current_user.business_id)
    return APIResponse(success=True, data=person)


@router.get("/{person_id}", response_model=APIResponse[PersonOut])
async def get_person(
    person_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    person = await person_service.get_person(person_id, current_user.business_id)
    return APIResponse(success=True, data=person)


@router.patch("/{person_id}", response_model=APIResponse[PersonOut])
async def update_person(
    person_id: str,
    body: UpdatePersonRequest,
    request: Request,
    current_user: CurrentUser = Depends(require_role("staff")),
    ip: Optional[str] = Depends(get_client_ip),
):
    person = await person_service.update_person(
        person_id, body, current_user.business_id, current_user.user_id, ip=ip
    )
    return APIResponse(success=True, data=person)


@router.delete("/{person_id}", response_model=APIResponse[None])
async def deactivate_person(
    person_id: str,
    request: Request,
    current_user: CurrentUser = Depends(require_role("admin")),
    ip: Optional[str] = Depends(get_client_ip),
):
    await person_service.deactivate_person(
        person_id, current_user.business_id, current_user.user_id, ip=ip
    )
    return APIResponse(success=True, data=None)
