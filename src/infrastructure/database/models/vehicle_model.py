from sqlalchemy import UUID, Column, DateTime, ForeignKey, Integer, String, func

from .base import Base


class VehicleModel(Base):
    __tablename__ = "vehicles"

    id = Column(UUID, primary_key=True)
    customer_id = Column(UUID, ForeignKey("customers.id"), nullable=False)
    brand = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False)
    year = Column(Integer, nullable=False)
    plate = Column(String(20), nullable=False, unique=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )
