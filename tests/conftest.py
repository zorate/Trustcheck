import asyncio
import os
import pytest
import pytest_asyncio
from beanie import init_beanie
from mongomock_motor import AsyncMongoMockClient

os.environ.setdefault("SECRET_KEY", "test-secret-key-that-is-long-enough-for-testing-purposes")
os.environ.setdefault("PHONE_HASH_SALT", "test-salt-that-is-long-enough")
os.environ.setdefault("MONGODB_URL", "mongodb://localhost:27017")
os.environ.setdefault("MONGODB_DB_NAME", "trustcheck_test")

from app.models.audit_log import AuditLog
from app.models.business import Business
from app.models.business_user import BusinessUser
from app.models.payment_record import PaymentRecord
from app.models.person import Person
from app.models.reference import Reference
from app.models.relationship import Relationship
from app.models.trust_score import TrustScore


@pytest_asyncio.fixture(scope="function")
async def init_test_db():
    client = AsyncMongoMockClient()
    await init_beanie(
        database=client["trustcheck_test"],
        document_models=[Business, BusinessUser, Person, Relationship,
                         PaymentRecord, TrustScore, Reference, AuditLog],
    )
    yield
    for model in [Business, BusinessUser, Person, Relationship,
                  PaymentRecord, TrustScore, Reference, AuditLog]:
        await model.delete_all()