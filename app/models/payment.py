from sqlalchemy import Column, String, ForeignKey, Numeric, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from app.models.base import Base

class PaymentStatus(str, enum.Enum):
    pending = "pending"
    paid = "paid"
    late = "late"
    defaulted = "defaulted"

class PaymentRecord(Base):
    business_id = Column(ForeignKey("business.id", ondelete="CASCADE"), nullable=False)
    person_id = Column(ForeignKey("person.id", ondelete="CASCADE"), nullable=False)
    relationship_id = Column(ForeignKey("relationship.id", ondelete="CASCADE"), nullable=False)

    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(8), nullable=False, default="NGN")
    due_date = Column(DateTime(timezone=True), nullable=False)
    paid_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.pending)

    business = relationship("Business", lazy="joined")
    person = relationship("Person", lazy="joined")
    relationship = relationship("Relationship", lazy="joined")
