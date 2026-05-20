from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class Customer:
    id: UUID
    name: str
    cpf_cnpj: str | None
    email: str
    phone: str
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
