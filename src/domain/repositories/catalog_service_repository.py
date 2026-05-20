from abc import ABC, abstractmethod
from uuid import UUID

from ..entities import CatalogService


class CatalogServiceRepository(ABC):
    @abstractmethod
    async def create(self, service: CatalogService) -> None:
        pass

    @abstractmethod
    async def update(self, service: CatalogService) -> None:
        pass

    @abstractmethod
    async def delete(self, service_id: UUID) -> bool:
        pass

    @abstractmethod
    async def get_by_id(self, service_id: UUID) -> CatalogService | None:
        pass

    @abstractmethod
    async def list(self) -> list[CatalogService]:
        pass
