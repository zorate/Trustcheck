from sqlalchemy import Column, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import Base

class Person(Base):
    # Phone is stored hashed for privacy; raw phone never stored
    phone_hash = Column(String(128), nullable=False)
    first_name = Column(String(128), nullable=True)
    last_name = Column(String(128), nullable=True)
    notes = Column(String(1024), nullable=True)

    # Person is global, but relationships are per business
    __table_args__ = (
        UniqueConstraint("phone_hash", name="uq_person_phone_hash"),
    )

class Relationship(Base):
    business_id = Column(ForeignKey("business.id", ondelete="CASCADE"), nullable=False)
    person_id = Column(ForeignKey("person.id", ondelete="CASCADE"), nullable=False)
    started_on = Column(String(32), nullable=False)  # ISO date string for simplicity
    status = Column(String(32), nullable=False, default="active")  # active, inactive

    business = relationship("Business", lazy="joined")
    person = relationship("Person", lazy="joined")
