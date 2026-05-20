from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities import CatalogService
from src.domain.repositories import CatalogServiceRepository
from src.infrastructure.database.models.catalog_service_model import CatalogServiceModel


class PostgresCatalogServiceRepository(CatalogServiceRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, service: CatalogService) -> None:
        model = CatalogServiceModel(
            id=service.id,
            description=service.description,
            price=service.price,
            created_at=service.created_at,
            updated_at=service.updated_at,
        )
        self.session.add(model)
        await self.session.commit()

    async def update(self, service: CatalogService) -> None:
        result = await self.session.execute(
            select(CatalogServiceModel).where(CatalogServiceModel.id == service.id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return

        model.description = service.description
        model.price = service.price
        model.updated_at = service.updated_at
        await self.session.commit()

    async def delete(self, service_id: UUID) -> bool:
        result = await self.session.execute(
            delete(CatalogServiceModel).where(CatalogServiceModel.id == service_id)
        )
        await self.session.commit()
        return (result.rowcount or 0) > 0

    async def get_by_id(self, service_id: UUID) -> CatalogService | None:
        result = await self.session.execute(
            select(CatalogServiceModel).where(CatalogServiceModel.id == service_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return CatalogService(
            id=model.id,
            description=model.description,
            price=float(model.price),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def list(self) -> list[CatalogService]:
        result = await self.session.execute(
            select(CatalogServiceModel).order_by(CatalogServiceModel.description.asc())
        )
        models = result.scalars().all()
        return [
            CatalogService(
                id=m.id,
                description=m.description,
                price=float(m.price),
                created_at=m.created_at,
                updated_at=m.updated_at,
            )
            for m in models
        ]
