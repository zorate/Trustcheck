import logging
import re
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status

from app.core.security import hash_phone
from app.models.person import Person
from app.models.relationship import Relationship
from app.schemas.person import AddPersonRequest, PersonOut, UpdatePersonRequest
from app.services.audit_service import write_audit

logger = logging.getLogger(__name__)


def _phone_display(phone: str) -> str:
    digits = re.sub(r"\D", "", phone)
    return f"****{digits[-4:]}" if len(digits) >= 4 else "****"


async def add_person(req: AddPersonRequest, business_id: str,
                     actor_id: str, ip: Optional[str] = None) -> PersonOut:
    phone_hash = hash_phone(req.phone)
    existing = await Person.find_one(
        Person.business_id == business_id,
        Person.phone_hash == phone_hash,
        Person.deleted_at == None,  # noqa: E711
    )

    if existing:
        updated = False
        if req.full_name and existing.full_name != req.full_name:
            existing.full_name = req.full_name
            updated = True
        if req.capacity_level and existing.capacity_level != req.capacity_level:
            existing.capacity_level = req.capacity_level
            updated = True
        if updated:
            existing.updated_at = datetime.now(timezone.utc)
            await existing.save()
        person = existing
    else:
        person = Person(business_id=business_id, phone_hash=phone_hash,
                        phone_display=_phone_display(req.phone),
                        full_name=req.full_name, capacity_level=req.capacity_level,
                        notes=req.notes)
        await person.insert()

    relationship = Relationship(business_id=business_id, person_id=person.id,
                                relationship_type=req.relationship_type,
                                relationship_start=req.relationship_start)
    await relationship.insert()
    await write_audit(action="person.create", business_id=business_id, actor_id=actor_id,
                      resource_type="person", resource_id=person.id,
                      detail={"relationship_type": req.relationship_type}, ip_address=ip)
    return _person_out(person)


async def get_person(person_id: str, business_id: str) -> PersonOut:
    return _person_out(await _get_person_scoped(person_id, business_id))


async def get_person_by_phone(phone: str, business_id: str) -> PersonOut:
    phone_hash = hash_phone(phone)
    person = await Person.find_one(
        Person.business_id == business_id,
        Person.phone_hash == phone_hash,
        Person.deleted_at == None,  # noqa: E711
    )
    if not person:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")
    return _person_out(person)


async def update_person(person_id: str, req: UpdatePersonRequest, business_id: str,
                        actor_id: str, ip: Optional[str] = None) -> PersonOut:
    person = await _get_person_scoped(person_id, business_id)
    if req.full_name is not None:
        person.full_name = req.full_name
    if req.capacity_level is not None:
        person.capacity_level = req.capacity_level
    if req.notes is not None:
        person.notes = req.notes
    person.updated_at = datetime.now(timezone.utc)
    await person.save()
    await write_audit(action="person.update", business_id=business_id, actor_id=actor_id,
                      resource_type="person", resource_id=person_id, ip_address=ip)
    return _person_out(person)


async def list_persons(business_id: str, page: int = 1,
                       page_size: int = 20) -> tuple[list[PersonOut], int]:
    skip = (page - 1) * page_size
    query = Person.find(Person.business_id == business_id,
                        Person.deleted_at == None,  # noqa: E711
                        Person.is_active == True)
    total = await query.count()
    persons = await query.skip(skip).limit(page_size).to_list()
    return [_person_out(p) for p in persons], total


async def deactivate_person(person_id: str, business_id: str,
                            actor_id: str, ip: Optional[str] = None) -> None:
    person = await _get_person_scoped(person_id, business_id)
    now = datetime.now(timezone.utc)
    person.is_active = False
    person.deleted_at = now
    person.updated_at = now
    await person.save()
    await write_audit(action="person.deactivate", business_id=business_id, actor_id=actor_id,
                      resource_type="person", resource_id=person_id, ip_address=ip)


async def _get_person_scoped(person_id: str, business_id: str) -> Person:
    person = await Person.find_one(
        Person.id == person_id,
        Person.business_id == business_id,
        Person.deleted_at == None,  # noqa: E711
    )
    if not person:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")
    return person


def _person_out(p: Person) -> PersonOut:
    return PersonOut(id=p.id, business_id=p.business_id, phone_display=p.phone_display,
                     full_name=p.full_name, capacity_level=p.capacity_level,
                     notes=p.notes, is_active=p.is_active,
                     created_at=p.created_at, updated_at=p.updated_at)