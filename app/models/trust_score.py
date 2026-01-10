from sqlalchemy import Column, ForeignKey, Integer, String, JSON
from sqlalchemy.orm import relationship
from app.models.base import Base

class TrustScore(Base):
    business_id = Column(ForeignKey("business.id", ondelete="CASCADE"), nullable=False)
    person_id = Column(ForeignKey("person.id", ondelete="CASCADE"), nullable=False)

    score = Column(Integer, nullable=False)
    risk_band = Column(String(32), nullable=False)
    recommendation = Column(String(128), nullable=False)
    breakdown = Column(JSON, nullable=False)

    business = relationship("Business", lazy="joined")
    person = relationship("Person", lazy="joined")
