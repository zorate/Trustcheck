from sqlalchemy import Column, String, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.models.base import Base

class AuditLog(Base):
    business_id = Column(ForeignKey("business.id", ondelete="CASCADE"), nullable=True)
    user_id = Column(ForeignKey("businessuser.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(128), nullable=False)
    path = Column(String(255), nullable=False)
    method = Column(String(16), nullable=False)
    ip = Column(String(64), nullable=True)
    details = Column(JSON, nullable=True)

    business = relationship("Business", lazy="joined")
    user = relationship("BusinessUser", lazy="joined")
