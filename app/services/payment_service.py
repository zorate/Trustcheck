import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status

from app.models.payment_record import PaymentRecord
from app.models.person import Person
from app.models.relationship import Relationship
from app.schemas.payment import PaymentOut, RecordPaymentRequest, UpdatePaymentStatusRequest
from app.services.audit_service import write_audit

logger = logging.getLogger(__name__)


async def record_payment(req: RecordPaymentRequest, business_id: str,
                         actor_id: str, ip: Optional[str] = None) -> PaymentOut:
    person = await Person.find_one(Person.id == req.person_id,
                                   Person.business_id == business_id,
                                   Person.deleted_at == None)  # noqa: E711
    if not person:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")

    rel = await Relationship.find_one(Relationship.id == req.relationship_id,
                                      Relationship.business_id == business_id,
                                      Relationship.person_id == req.person_id,
                                      Relationship.deleted_at == None)  # noqa: E711
    if not rel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relationship not found")

    payment = PaymentRecord(business_id=business_id, person_id=req.person_id,
                            relationship_id=req.relationship_id, amount=req.amount,
                            currency=req.currency, description=req.description,
                            due_date=req.due_date, paid_date=req.paid_date,
                            status=req.status, created_by=actor_id)
    await payment.insert()
    await write_audit(action="payment.create", business_id=business_id, actor_id=actor_id,
                      resource_type="payment_record", resource_id=payment.id,
                      detail={"status": req.status, "currency": req.currency}, ip_address=ip)
    return _payment_out(payment)


async def update_payment_status(payment_id: str, req: UpdatePaymentStatusRequest,
                                business_id: str, actor_id: str,
                                ip: Optional[str] = None) -> PaymentOut:
    payment = await _get_payment_scoped(payment_id, business_id)
    payment.status = req.status
    if req.paid_date is not None:
        payment.paid_date = req.paid_date
    payment.updated_by = actor_id
    payment.updated_at = datetime.now(timezone.utc)
    await payment.save()
    await write_audit(action="payment.status_update", business_id=business_id, actor_id=actor_id,
                      resource_type="payment_record", resource_id=payment_id,
                      detail={"new_status": req.status}, ip_address=ip)
    return _payment_out(payment)


async def get_payment(payment_id: str, business_id: str) -> PaymentOut:
    return _payment_out(await _get_payment_scoped(payment_id, business_id))


async def list_payments_for_person(person_id: str, business_id: str, page: int = 1,
                                   page_size: int = 20,
                                   status_filter: Optional[str] = None) -> tuple[list[PaymentOut], int]:
    person = await Person.find_one(Person.id == person_id,
                                   Person.business_id == business_id,
                                   Person.deleted_at == None)  # noqa: E711
    if not person:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")

    filters = [PaymentRecord.business_id == business_id,
               PaymentRecord.person_id == person_id,
               PaymentRecord.deleted_at == None]  # noqa: E711
    if status_filter:
        filters.append(PaymentRecord.status == status_filter)

    skip = (page - 1) * page_size
    query = PaymentRecord.find(*filters)
    total = await query.count()
    records = await query.sort(-PaymentRecord.due_date).skip(skip).limit(page_size).to_list()
    return [_payment_out(r) for r in records], total


async def _get_payment_scoped(payment_id: str, business_id: str) -> PaymentRecord:
    payment = await PaymentRecord.find_one(PaymentRecord.id == payment_id,
                                           PaymentRecord.business_id == business_id,
                                           PaymentRecord.deleted_at == None)  # noqa: E711
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return payment


def _payment_out(p: PaymentRecord) -> PaymentOut:
    return PaymentOut(id=p.id, business_id=p.business_id, person_id=p.person_id,
                      relationship_id=p.relationship_id, amount=p.amount, currency=p.currency,
                      description=p.description, due_date=p.due_date, paid_date=p.paid_date,
                      status=p.status, created_by=p.created_by,
                      created_at=p.created_at, updated_at=p.updated_at)