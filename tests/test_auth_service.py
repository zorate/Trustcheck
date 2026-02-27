"""
Integration tests for auth service using in-memory MongoDB.
"""
import pytest
import pytest_asyncio
from fastapi import HTTPException

from tests.conftest import init_test_db  # noqa: F401
from app.schemas.auth import BusinessRegisterRequest, LoginRequest
from app.services import auth_service


REGISTER_DATA = BusinessRegisterRequest(
    business_name="Test SME Ltd",
    business_type="sme",
    email="owner@testsme.ng",
    password="Str0ngPassword1",
    full_name="Test Owner",
)


@pytest.mark.asyncio
async def test_register_business(init_test_db):
    result = await auth_service.register_business(REGISTER_DATA)
    assert result.user.email == "owner@testsme.ng"
    assert result.user.role == "owner"
    assert result.tokens.access_token
    assert result.tokens.refresh_token


@pytest.mark.asyncio
async def test_register_duplicate_email_raises(init_test_db):
    await auth_service.register_business(REGISTER_DATA)
    with pytest.raises(HTTPException) as exc:
        await auth_service.register_business(REGISTER_DATA)
    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_login_success(init_test_db):
    await auth_service.register_business(REGISTER_DATA)
    result = await auth_service.login(
        LoginRequest(email="owner@testsme.ng", password="Str0ngPassword1")
    )
    assert result.tokens.access_token
    assert result.user.email == "owner@testsme.ng"


@pytest.mark.asyncio
async def test_login_wrong_password(init_test_db):
    await auth_service.register_business(REGISTER_DATA)
    with pytest.raises(HTTPException) as exc:
        await auth_service.login(
            LoginRequest(email="owner@testsme.ng", password="WrongPassword1")
        )
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(init_test_db):
    with pytest.raises(HTTPException) as exc:
        await auth_service.login(
            LoginRequest(email="nobody@example.com", password="Str0ngPassword1")
        )
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(init_test_db):
    reg = await auth_service.register_business(REGISTER_DATA)
    tokens = await auth_service.refresh_tokens(reg.tokens.refresh_token)
    assert tokens.access_token
    assert tokens.access_token != reg.tokens.access_token


@pytest.mark.asyncio
async def test_refresh_with_access_token_fails(init_test_db):
    reg = await auth_service.register_business(REGISTER_DATA)
    with pytest.raises(HTTPException) as exc:
        await auth_service.refresh_tokens(reg.tokens.access_token)  # wrong token type
    assert exc.value.status_code == 401