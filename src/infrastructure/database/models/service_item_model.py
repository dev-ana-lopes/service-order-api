from sqlalchemy import UUID, Column, DateTime, ForeignKey, Numeric, String, func

from .base import Base


class ServiceItemModel(Base):
    __tablename__ = "service_items"

    id = Column(UUID, primary_key=True)
    service_order_id = Column(UUID, ForeignKey("service_orders.id"), nullable=False)
    description = Column(String(500), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
