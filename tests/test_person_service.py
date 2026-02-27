"""
Tests for person service — verifying tenant isolation and phone hashing.
"""
from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from tests.conftest import init_test_db  # noqa: F401
from app.schemas.auth import BusinessRegisterRequest
from app.schemas.person import AddPersonRequest, UpdatePersonRequest
from app.services import auth_service, person_service


async def _register(email: str, name: str):
    return await auth_service.register_business(
        BusinessRegisterRequest(
            business_name=name,
            business_type="sme",
            email=email,
            password="Str0ngPassword1",
            full_name="Owner",
        )
    )


ADD_PERSON = AddPersonRequest(
    full_name="Emeka Obi",
    phone="08012345678",
    capacity_level="basic",
    relationship_type="customer",
    relationship_start=datetime(2024, 1, 1, tzinfo=timezone.utc),
)


@pytest.mark.asyncio
async def test_add_person(init_test_db):
    reg = await _register("biz1@test.ng", "Biz 1")
    person = await person_service.add_person(ADD_PERSON, reg.user.business_id, reg.user.id)

    assert person.full_name == "Emeka Obi"
    assert "****" in person.phone_display
    assert "5678" in person.phone_display  # last 4 digits
    assert person.business_id == reg.user.business_id


@pytest.mark.asyncio
async def test_phone_not_stored_raw(init_test_db):
    reg = await _register("biz2@test.ng", "Biz 2")
    person = await person_service.add_person(ADD_PERSON, reg.user.business_id, reg.user.id)

    # Only last 4 digits stored — never full phone
    assert person.phone_display == "****5678"


@pytest.mark.asyncio
async def test_lookup_by_phone(init_test_db):
    reg = await _register("biz3@test.ng", "Biz 3")
    await person_service.add_person(ADD_PERSON, reg.user.business_id, reg.user.id)

    found = await person_service.get_person_by_phone("08012345678", reg.user.business_id)
    assert found.full_name == "Emeka Obi"


@pytest.mark.asyncio
async def test_cross_tenant_isolation(init_test_db):
    """Person in Biz A must not be accessible from Biz B."""
    reg_a = await _register("biza@test.ng", "Biz A")
    reg_b = await _register("bizb@test.ng", "Biz B")

    person = await person_service.add_person(ADD_PERSON, reg_a.user.business_id, reg_a.user.id)

    # Biz B cannot access Biz A's person by ID
    with pytest.raises(HTTPException) as exc:
        await person_service.get_person(person.id, reg_b.user.business_id)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_phone_lookup_scoped_to_tenant(init_test_db):
    """Same phone number in two businesses — separate records."""
    reg_a = await _register("biza2@test.ng", "Biz A2")
    reg_b = await _register("bizb2@test.ng", "Biz B2")

    await person_service.add_person(ADD_PERSON, reg_a.user.business_id, reg_a.user.id)

    # Biz B cannot find Biz A's person by phone
    with pytest.raises(HTTPException) as exc:
        await person_service.get_person_by_phone("08012345678", reg_b.user.business_id)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_update_person(init_test_db):
    reg = await _register("biz4@test.ng", "Biz 4")
    person = await person_service.add_person(ADD_PERSON, reg.user.business_id, reg.user.id)

    updated = await person_service.update_person(
        person.id,
        UpdatePersonRequest(full_name="Emeka Updated", capacity_level="verified"),
        reg.user.business_id,
        reg.user.id,
    )
    assert updated.full_name == "Emeka Updated"
    assert updated.capacity_level == "verified"


@pytest.mark.asyncio
async def test_idempotent_add_same_phone(init_test_db):
    """Adding same phone twice returns existing person."""
    reg = await _register("biz5@test.ng", "Biz 5")
    p1 = await person_service.add_person(ADD_PERSON, reg.user.business_id, reg.user.id)
    p2 = await person_service.add_person(ADD_PERSON, reg.user.business_id, reg.user.id)
    assert p1.id == p2.id