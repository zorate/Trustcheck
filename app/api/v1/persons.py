from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.rate_limit import rate_limit
from app.schemas.person import AddPersonRequest, UpdatePersonRequest, PersonResponse, RelationshipRequest, RelationshipResponse
from app.models.person import Person, Relationship
from app.middleware.auth import get_current_user
from app.services.hashing import hash_phone

router = APIRouter(prefix="/api/v1/persons", tags=["persons"])

@router.post("/", response_model=PersonResponse)
async def add_person(payload: AddPersonRequest, request: Request, db: AsyncSession = Depends(get_db)):
    rate_limit(request)
    await get_current_user(request)
    phone_hash = hash_phone(payload.phone)
    q = select(Person).where(Person.phone_hash == phone_hash, Person.deleted == False)
    existing = (await db.execute(q)).scalars().first()
    if existing:
        # Update names if provided
        if payload.first_name:
            existing.first_name = payload.first_name
        if payload.last_name:
            existing.last_name = payload.last_name
        if payload.notes:
            existing.notes = payload.notes
        await db.commit()
        return PersonResponse(id=existing.id, first_name=existing.first_name, last_name=existing.last_name)
    person = Person(phone_hash=phone_hash, first_name=payload.first_name, last_name=payload.last_name, notes=payload.notes)
    db.add(person)
    await db.commit()
    return PersonResponse(id=person.id, first_name=person.first_name, last_name=person.last_name)

@router.put("/{person_id}", response_model=PersonResponse)
async def update_person(person_id: str, payload: UpdatePersonRequest, request: Request, db: AsyncSession = Depends(get_db)):
    rate_limit(request)
    await get_current_user(request)
    q = select(Person).where(Person.id == person_id, Person.deleted == False)
    person = (await db.execute(q)).scalars().first()
    if not person:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")
    if payload.first_name is not None:
        person.first_name = payload.first_name
    if payload.last_name is not None:
        person.last_name = payload.last_name
    if payload.notes is not None:
        person.notes = payload.notes
    await db.commit()
    return PersonResponse(id=person.id, first_name=person.first_name, last_name=person.last_name)

@router.post("/relationships", response_model=RelationshipResponse)
async def create_relationship(payload: RelationshipRequest, request: Request, db: AsyncSession = Depends(get_db)):
    rate_limit(request)
    user = await get_current_user(request)
    rel = Relationship(business_id=user["bid"], person_id=payload.person_id, started_on=payload.started_on, status=payload.status)
    db.add(rel)
    await db.commit()
    return RelationshipResponse(id=rel.id, person_id=rel.person_id, started_on=rel.started_on, status=rel.status)
