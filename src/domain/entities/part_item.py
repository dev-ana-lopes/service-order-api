from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class PartItem:
    id: UUID
    service_order_id: UUID
    name: str
    price: float
    quantity: int
    created_at: datetime
