from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.part_item import PartItem
from src.domain.repositories.part_item_repository import PartItemRepository

from ..models.part_item_model import PartItemModel


class PostgresPartItemRepository(PartItemRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, part_item: PartItem) -> None:
        model = PartItemModel(
            id=part_item.id,
            service_order_id=part_item.service_order_id,
            name=part_item.name,
            price=part_item.price,
            quantity=part_item.quantity,
            created_at=part_item.created_at,
        )
        self.session.add(model)
        await self.session.commit()

    async def save_many(self, part_items: list[PartItem]) -> None:
        models = [
            PartItemModel(
                id=item.id,
                service_order_id=item.service_order_id,
                name=item.name,
                price=item.price,
                quantity=item.quantity,
                created_at=item.created_at,
            )
            for item in part_items
        ]
        self.session.add_all(models)
        await self.session.commit()

    async def get_by_service_order_id(self, service_order_id: UUID) -> list[PartItem]:
        query = select(PartItemModel).where(
            PartItemModel.service_order_id == service_order_id
        )
        result = await self.session.execute(query)
        models = result.scalars().all()

        return [
            PartItem(
                id=model.id,
                service_order_id=model.service_order_id,
                name=model.name,
                price=float(model.price),
                quantity=model.quantity,
                created_at=model.created_at,
            )
            for model in models
        ]
