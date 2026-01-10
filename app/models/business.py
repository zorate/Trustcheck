from sqlalchemy import Column, String, UniqueConstraint
from app.models.base import Base

class Business(Base):
    name = Column(String(255), nullable=False)
    country = Column(String(64), nullable=False, default="Nigeria")
    phone = Column(String(32), nullable=True)
    email = Column(String(255), nullable=True)

    __table_args__ = (
        UniqueConstraint("name", "country", name="uq_business_name_country"),
    )
