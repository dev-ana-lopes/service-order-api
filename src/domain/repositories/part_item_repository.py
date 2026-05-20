from abc import ABC, abstractmethod
from uuid import UUID

from ..entities import PartItem


class PartItemRepository(ABC):
    @abstractmethod
    async def save(self, part_item: PartItem) -> None:
        pass

    @abstractmethod
    async def save_many(self, part_items: list[PartItem]) -> None:
        pass

    @abstractmethod
    async def get_by_service_order_id(self, service_order_id: UUID) -> list[PartItem]:
        pass
