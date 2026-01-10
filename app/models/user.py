from sqlalchemy import Column, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.models.base import Base

class BusinessUser(Base):
    business_id = Column(ForeignKey("business.id", ondelete="CASCADE"), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(32), nullable=True)
    full_name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    business = relationship("Business", lazy="joined")
