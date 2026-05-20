from uuid import UUID, uuid4

from ...domain.entities import CatalogService, InventoryPart
from ...domain.repositories import CatalogServiceRepository, InventoryPartRepository
from ...domain.time import utcnow


class CreateCatalogServiceUseCase:
    def __init__(self, repo: CatalogServiceRepository):
        self.repo = repo

    async def execute(self, description: str, price: float) -> str:
        now = utcnow()
        service = CatalogService(
            id=uuid4(),
            description=description,
            price=price,
            created_at=now,
            updated_at=now,
        )
        await self.repo.create(service)
        return str(service.id)


class UpdateCatalogServiceUseCase:
    def __init__(self, repo: CatalogServiceRepository):
        self.repo = repo

    async def execute(self, service_id: UUID, description: str, price: float) -> bool:
        existing = await self.repo.get_by_id(service_id)
        if existing is None:
            return False
        existing.description = description
        existing.price = price
        existing.updated_at = utcnow()
        await self.repo.update(existing)
        return True


class DeleteCatalogServiceUseCase:
    def __init__(self, repo: CatalogServiceRepository):
        self.repo = repo

    async def execute(self, service_id: UUID) -> bool:
        return await self.repo.delete(service_id)


class ListCatalogServicesUseCase:
    def __init__(self, repo: CatalogServiceRepository):
        self.repo = repo

    async def execute(self) -> list[CatalogService]:
        return await self.repo.list()


class GetCatalogServiceUseCase:
    def __init__(self, repo: CatalogServiceRepository):
        self.repo = repo

    async def execute(self, service_id: UUID) -> CatalogService | None:
        return await self.repo.get_by_id(service_id)


class CreateInventoryPartUseCase:
    def __init__(self, repo: InventoryPartRepository):
        self.repo = repo

    async def execute(self, name: str, unit_price: float, stock_quantity: int) -> str:
        now = utcnow()
        existing = await self.repo.get_by_name(name)
        if existing is not None:
            raise ValueError("Part name already registered")
        part = InventoryPart(
            id=uuid4(),
            name=name,
            unit_price=unit_price,
            stock_quantity=stock_quantity,
            created_at=now,
            updated_at=now,
        )
        await self.repo.create(part)
        return str(part.id)


class UpdateInventoryPartUseCase:
    def __init__(self, repo: InventoryPartRepository):
        self.repo = repo

    async def execute(
        self, part_id: UUID, name: str, unit_price: float, stock_quantity: int
    ) -> bool:
        existing = await self.repo.get_by_id(part_id)
        if existing is None:
            return False
        if name != existing.name:
            other = await self.repo.get_by_name(name)
            if other is not None and other.id != part_id:
                raise ValueError("Part name already registered")
        existing.name = name
        existing.unit_price = unit_price
        existing.stock_quantity = stock_quantity
        existing.updated_at = utcnow()
        await self.repo.update(existing)
        return True


class DeleteInventoryPartUseCase:
    def __init__(self, repo: InventoryPartRepository):
        self.repo = repo

    async def execute(self, part_id: UUID) -> bool:
        return await self.repo.delete(part_id)


class ListInventoryPartsUseCase:
    def __init__(self, repo: InventoryPartRepository):
        self.repo = repo

    async def execute(self) -> list[InventoryPart]:
        return await self.repo.list()


class GetInventoryPartUseCase:
    def __init__(self, repo: InventoryPartRepository):
        self.repo = repo

    async def execute(self, part_id: UUID) -> InventoryPart | None:
        return await self.repo.get_by_id(part_id)
