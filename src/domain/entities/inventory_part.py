from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class InventoryPart:
    id: UUID
    name: str
    unit_price: float
    stock_quantity: int
    created_at: datetime
    updated_at: datetime
