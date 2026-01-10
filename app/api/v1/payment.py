from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.rate_limit import rate_limit
from app.schemas.payment import RecordPaymentRequest, UpdatePaymentStatusRequest, PaymentResponse
from app.models.payment import PaymentRecord, PaymentStatus
from app.middleware.auth import get_current_user
from app.utils.pagination import get_pagination

router = APIRouter(prefix="/api/v1/payments", tags=["payments"])

@router.post("/", response_model=PaymentResponse)
async def record_payment(payload: RecordPaymentRequest, request: Request, db: AsyncSession = Depends(get_db)):
    rate_limit(request)
    user = await get_current_user(request)
    payment = PaymentRecord(
        business_id=user["bid"],
        person_id=payload.person_id,
        relationship_id=payload.relationship_id,
        amount=payload.amount,
        currency=payload.currency,
        due_date=payload.due_date,
        status=PaymentStatus.pending,
    )
    db.add(payment)
    await db.commit()
    return PaymentResponse(
        id=payment.id,
        relationship_id=payment.relationship_id,
        person_id=payment.person_id,
        amount=float(payment.amount),
        currency=payment.currency,
        due_date=payment.due_date,
        paid_date=payment.paid_date,
        status=payment.status.value,
    )

@router.put("/{payment_id}/status", response_model=PaymentResponse)
async def update_payment_status(payment_id: str, payload: UpdatePaymentStatusRequest, request: Request, db: AsyncSession = Depends(get_db)):
    rate_limit(request)
    user = await get_current_user(request)
    q = select(PaymentRecord).where(PaymentRecord.id == payment_id, PaymentRecord.deleted == False)
    payment = (await db.execute(q)).scalars().first()
    if not payment or str(payment.business_id) != str(user["bid"]):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    payment.status = PaymentStatus(payload.status)
    payment.paid_date = payload.paid_date
    await db.commit()
    return PaymentResponse(
        id=payment.id,
        relationship_id=payment.relationship_id,
        person_id=payment.person_id,
        amount=float(payment.amount),
        currency=payment.currency,
        due_date=payment.due_date,
        paid_date=payment.paid_date,
        status=payment.status.value,
    )

@router.get("/", response_model=list[PaymentResponse])
async def list_payments(request: Request, limit: int | None = None, offset: int | None = None, db: AsyncSession = Depends(get_db)):
    rate_limit(request)
    user = await get_current_user(request)
    l, o = get_pagination(limit, offset)
    q = select(PaymentRecord).where(PaymentRecord.business_id == user["bid"], PaymentRecord.deleted == False).offset(o).limit(l)
    payments = (await db.execute(q)).scalars().all()
    return [
        PaymentResponse(
            id=p.id,
            relationship_id=p.relationship_id,
            person_id=p.person_id,
            amount=float(p.amount),
            currency=p.currency,
            due_date=p.due_date,
            paid_date=p.paid_date,
            status=p.status.value,
        ) for p in payments
    ]
