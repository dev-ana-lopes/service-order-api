from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class Vehicle:
    id: UUID
    customer_id: UUID
    brand: str
    model: str
    year: int
    plate: str
    created_at: datetime
    updated_at: datetime
