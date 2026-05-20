from abc import ABC, abstractmethod
from uuid import UUID

from ..entities import InventoryPart


class InventoryPartRepository(ABC):
    @abstractmethod
    async def create(self, part: InventoryPart) -> None:
        pass

    @abstractmethod
    async def update(self, part: InventoryPart) -> None:
        pass

    @abstractmethod
    async def delete(self, part_id: UUID) -> bool:
        pass

    @abstractmethod
    async def get_by_id(self, part_id: UUID) -> InventoryPart | None:
        pass

    @abstractmethod
    async def get_by_name(self, name: str) -> InventoryPart | None:
        pass

    @abstractmethod
    async def list(self) -> list[InventoryPart]:
        pass

    @abstractmethod
    async def decrease_stock(self, part_id: UUID, quantity: int) -> bool:
        pass
