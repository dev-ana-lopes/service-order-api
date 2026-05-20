from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.service_item import ServiceItem
from src.domain.repositories.service_item_repository import ServiceItemRepository

from ..models.service_item_model import ServiceItemModel


class PostgresServiceItemRepository(ServiceItemRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, service_item: ServiceItem) -> None:
        model = ServiceItemModel(
            id=service_item.id,
            service_order_id=service_item.service_order_id,
            description=service_item.description,
            price=service_item.price,
            created_at=service_item.created_at,
        )
        self.session.add(model)
        await self.session.commit()

    async def save_many(self, service_items: list[ServiceItem]) -> None:
        models = [
            ServiceItemModel(
                id=item.id,
                service_order_id=item.service_order_id,
                description=item.description,
                price=item.price,
                created_at=item.created_at,
            )
            for item in service_items
        ]
        self.session.add_all(models)
        await self.session.commit()

    async def get_by_service_order_id(self, service_order_id: UUID) -> list[ServiceItem]:
        query = select(ServiceItemModel).where(
            ServiceItemModel.service_order_id == service_order_id
        )
        result = await self.session.execute(query)
        models = result.scalars().all()

        return [
            ServiceItem(
                id=model.id,
                service_order_id=model.service_order_id,
                description=model.description,
                price=float(model.price),
                created_at=model.created_at,
            )
            for model in models
        ]
