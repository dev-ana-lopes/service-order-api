from sqlalchemy import UUID, Boolean, Column, DateTime, String, func

from .base import Base


class CustomerModel(Base):
    __tablename__ = "customers"

    id = Column(UUID, primary_key=True)
    name = Column(String(255), nullable=False)
    cpf_cnpj = Column(String(14), nullable=True, unique=True)
    email = Column(String(255), nullable=False, unique=True)
    phone = Column(String(20), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )
