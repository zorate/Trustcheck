from sqlalchemy import Column, String, ForeignKey, Integer
from sqlalchemy.orm import relationship
from app.models.base import Base

class Reference(Base):
    business_id = Column(ForeignKey("business.id", ondelete="CASCADE"), nullable=False)
    person_id = Column(ForeignKey("person.id", ondelete="CASCADE"), nullable=False)

    level = Column(Integer, nullable=False)  # 0 none, 1 informal, 2 trusted/guarantor
    source = Column(String(255), nullable=True)  # who endorsed
    notes = Column(String(1024), nullable=True)

    business = relationship("Business", lazy="joined")
    person = relationship("Person", lazy="joined")
