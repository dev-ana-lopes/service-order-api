from sqlalchemy import UUID, Column, DateTime, Numeric, String, func

from .base import Base


class CatalogServiceModel(Base):
    __tablename__ = "catalog_services"

    id = Column(UUID, primary_key=True)
    description = Column(String(500), nullable=False, unique=True)
    price = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )
