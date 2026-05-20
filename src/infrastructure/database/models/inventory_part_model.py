from sqlalchemy import UUID, Column, DateTime, Integer, Numeric, String, func

from .base import Base


class InventoryPartModel(Base):
    __tablename__ = "inventory_parts"

    id = Column(UUID, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    unit_price = Column(Numeric(10, 2), nullable=False)
    stock_quantity = Column(Integer(), nullable=False, default=0)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )
