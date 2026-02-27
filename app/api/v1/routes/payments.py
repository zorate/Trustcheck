from typing import Optional
from fastapi import APIRouter, Depends, Query, Request
from app.api.deps import CurrentUser, get_client_ip, get_current_user, require_role
from app.schemas.common import APIResponse, PaginatedResponse
from app.schemas.payment import PaymentOut, RecordPaymentRequest, UpdatePaymentStatusRequest
from app.services import payment_service

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("", response_model=APIResponse[PaymentOut], status_code=201)
async def record_payment(body: RecordPaymentRequest, request: Request,
                         current_user: CurrentUser = Depends(require_role("staff")),
                         ip: Optional[str] = Depends(get_client_ip)):
    payment = await payment_service.record_payment(body, current_user.business_id,
                                                   current_user.user_id, ip=ip)
    return APIResponse(data=payment, message="Payment recorded")


@router.get("/person/{person_id}", response_model=PaginatedResponse[PaymentOut])
async def list_payments(person_id: str, page: int = Query(1, ge=1),
                        page_size: int = Query(20, ge=1, le=100),
                        status: Optional[str] = Query(None),
                        current_user: CurrentUser = Depends(get_current_user)):
    payments, total = await payment_service.list_payments_for_person(
        person_id, current_user.business_id, page=page, page_size=page_size, status_filter=status)
    return PaginatedResponse(data=payments, total=total, page=page, page_size=page_size,
                             has_more=(page * page_size) < total)


@router.get("/{payment_id}", response_model=APIResponse[PaymentOut])
async def get_payment(payment_id: str, current_user: CurrentUser = Depends(get_current_user)):
    return APIResponse(data=await payment_service.get_payment(payment_id,
                                                              current_user.business_id))


@router.patch("/{payment_id}/status", response_model=APIResponse[PaymentOut])
async def update_payment_status(payment_id: str, body: UpdatePaymentStatusRequest,
                                request: Request,
                                current_user: CurrentUser = Depends(require_role("staff")),
                                ip: Optional[str] = Depends(get_client_ip)):
    payment = await payment_service.update_payment_status(payment_id, body,
                                                          current_user.business_id,
                                                          current_user.user_id, ip=ip)
    return APIResponse(data=payment)