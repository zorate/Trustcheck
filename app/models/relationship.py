from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base

'''class Relationship(Base):
    business_id = Column(ForeignKey("business.id", ondelete="CASCADE"), nullable=False)
    person_id = Column(ForeignKey("person.id", ondelete="CASCADE"), nullable=False)
    started_on = Column(String(32), nullable=False)  # ISO date string
    status = Column(String(32), nullable=False, default="active")  # active, inactive

    business = relationship("Business", lazy="joined")
    person = relationship("Person", lazy="joined")'''
