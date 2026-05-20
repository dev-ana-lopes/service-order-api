from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class CatalogService:
    id: UUID
    description: str
    price: float
    created_at: datetime
    updated_at: datetime
