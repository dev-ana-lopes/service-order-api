from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from ..entities import Vehicle


class VehicleRepository(ABC):
    @abstractmethod
    async def save(self, vehicle: Vehicle) -> None:
        pass

    @abstractmethod
    async def update(self, vehicle: Vehicle) -> None:
        pass

    @abstractmethod
    async def delete(self, vehicle_id: UUID) -> bool:
        pass

    @abstractmethod
    async def get_by_id(self, vehicle_id: UUID) -> Vehicle | None:
        pass

    @abstractmethod
    async def get_by_plate(self, plate: str) -> Vehicle | None:
        pass

    @abstractmethod
    async def list(self) -> list[Vehicle]:
        pass

    @abstractmethod
    async def list_by_customer_id(self, customer_id: UUID) -> list[Vehicle]:
        pass
