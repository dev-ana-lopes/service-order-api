from abc import ABC, abstractmethod
from uuid import UUID

from ..entities import ServiceItem


class ServiceItemRepository(ABC):
    @abstractmethod
    async def save(self, service_item: ServiceItem) -> None:
        pass

    @abstractmethod
    async def save_many(self, service_items: list[ServiceItem]) -> None:
        pass

    @abstractmethod
    async def get_by_service_order_id(self, service_order_id: UUID) -> list[ServiceItem]:
        pass
