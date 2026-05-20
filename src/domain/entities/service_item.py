from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class ServiceItem:
    id: UUID
    service_order_id: UUID
    description: str
    price: float
    created_at: datetime
