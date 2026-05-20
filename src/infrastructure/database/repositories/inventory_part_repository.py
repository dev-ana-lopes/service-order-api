from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities import InventoryPart
from src.domain.repositories import InventoryPartRepository
from src.infrastructure.database.models.inventory_part_model import InventoryPartModel


class PostgresInventoryPartRepository(InventoryPartRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, part: InventoryPart) -> None:
        model = InventoryPartModel(
            id=part.id,
            name=part.name,
            unit_price=part.unit_price,
            stock_quantity=part.stock_quantity,
            created_at=part.created_at,
            updated_at=part.updated_at,
        )
        self.session.add(model)
        await self.session.commit()

    async def update(self, part: InventoryPart) -> None:
        result = await self.session.execute(
            select(InventoryPartModel).where(InventoryPartModel.id == part.id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return

        model.name = part.name
        model.unit_price = part.unit_price
        model.stock_quantity = part.stock_quantity
        model.updated_at = part.updated_at
        await self.session.commit()

    async def delete(self, part_id: UUID) -> bool:
        result = await self.session.execute(
            delete(InventoryPartModel).where(InventoryPartModel.id == part_id)
        )
        await self.session.commit()
        return (result.rowcount or 0) > 0

    async def get_by_id(self, part_id: UUID) -> InventoryPart | None:
        result = await self.session.execute(
            select(InventoryPartModel).where(InventoryPartModel.id == part_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return InventoryPart(
            id=model.id,
            name=model.name,
            unit_price=float(model.unit_price),
            stock_quantity=model.stock_quantity,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def get_by_name(self, name: str) -> InventoryPart | None:
        result = await self.session.execute(
            select(InventoryPartModel).where(InventoryPartModel.name == name)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return InventoryPart(
            id=model.id,
            name=model.name,
            unit_price=float(model.unit_price),
            stock_quantity=model.stock_quantity,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def list(self) -> list[InventoryPart]:
        result = await self.session.execute(
            select(InventoryPartModel).order_by(InventoryPartModel.name.asc())
        )
        models = result.scalars().all()
        return [
            InventoryPart(
                id=m.id,
                name=m.name,
                unit_price=float(m.unit_price),
                stock_quantity=m.stock_quantity,
                created_at=m.created_at,
                updated_at=m.updated_at,
            )
            for m in models
        ]

    async def decrease_stock(self, part_id: UUID, quantity: int) -> bool:
        if quantity <= 0:
            return True

        stmt = (
            update(InventoryPartModel)
            .where(
                InventoryPartModel.id == part_id,
                InventoryPartModel.stock_quantity >= quantity,
            )
            .values(stock_quantity=InventoryPartModel.stock_quantity - quantity)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return (result.rowcount or 0) > 0
