from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.part_item import PartItem
from src.domain.entities.service_item import ServiceItem
from src.domain.entities.service_order import ServiceOrder
from src.domain.enums import ApprovalDecision, ServiceOrderStatus
from src.domain.repositories.service_order_repository import ServiceOrderRepository
from src.domain.time import utcnow
from src.infrastructure.database.models.part_item_model import PartItemModel
from src.infrastructure.database.models.service_item_model import ServiceItemModel
from src.infrastructure.database.models.service_order_model import ServiceOrderModel


class PostgresServiceOrderRepository(ServiceOrderRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, service_order: ServiceOrder) -> None:
        model = ServiceOrderModel(
            id=service_order.id,
            customer_id=service_order.customer_id,
            vehicle_id=service_order.vehicle_id,
            status=service_order.status.value,
            started_at=service_order.started_at,
            finished_at=service_order.finished_at,
            approval_decision=(
                service_order.approval_decision.value
                if service_order.approval_decision is not None
                else None
            ),
            approval_decision_at=service_order.approval_decision_at,
            rejection_reason=service_order.rejection_reason,
            created_at=service_order.created_at,
            updated_at=service_order.updated_at,
        )
        self.session.add(model)
        await self.session.flush()

        if service_order.service_items:
            service_items = [
                ServiceItemModel(
                    id=item.id,
                    service_order_id=item.service_order_id,
                    description=item.description,
                    price=item.price,
                    created_at=item.created_at,
                )
                for item in service_order.service_items
            ]
            self.session.add_all(service_items)

        if service_order.part_items:
            part_items = [
                PartItemModel(
                    id=item.id,
                    service_order_id=item.service_order_id,
                    name=item.name,
                    price=item.price,
                    quantity=item.quantity,
                    created_at=item.created_at,
                )
                for item in service_order.part_items
            ]
            self.session.add_all(part_items)

        await self.session.commit()

    async def update(self, service_order: ServiceOrder) -> None:
        result = await self.session.execute(
            select(ServiceOrderModel).where(ServiceOrderModel.id == service_order.id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return

        model.customer_id = service_order.customer_id
        model.vehicle_id = service_order.vehicle_id
        model.status = service_order.status.value
        model.started_at = service_order.started_at
        model.finished_at = service_order.finished_at
        model.approval_decision = (
            service_order.approval_decision.value
            if service_order.approval_decision is not None
            else None
        )
        model.approval_decision_at = service_order.approval_decision_at
        model.rejection_reason = service_order.rejection_reason
        model.updated_at = service_order.updated_at
        await self.session.commit()

    async def get_by_id(self, service_order_id: UUID) -> ServiceOrder | None:
        query = select(ServiceOrderModel).where(ServiceOrderModel.id == service_order_id)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()

        if not model:
            return None

        service_items_query = select(ServiceItemModel).where(
            ServiceItemModel.service_order_id == service_order_id
        )
        service_items_result = await self.session.execute(service_items_query)
        service_items_models = service_items_result.scalars().all()

        part_items_query = select(PartItemModel).where(
            PartItemModel.service_order_id == service_order_id
        )
        part_items_result = await self.session.execute(part_items_query)
        part_items_models = part_items_result.scalars().all()

        service_items = [
            ServiceItem(
                id=item.id,
                service_order_id=item.service_order_id,
                description=item.description,
                price=float(item.price),
                created_at=item.created_at,
            )
            for item in service_items_models
        ]

        part_items = [
            PartItem(
                id=item.id,
                service_order_id=item.service_order_id,
                name=item.name,
                price=float(item.price),
                quantity=item.quantity,
                created_at=item.created_at,
            )
            for item in part_items_models
        ]

        return ServiceOrder(
            id=model.id,
            customer_id=model.customer_id,
            vehicle_id=model.vehicle_id,
            status=ServiceOrderStatus(model.status),
            created_at=model.created_at,
            updated_at=model.updated_at,
            started_at=model.started_at,
            finished_at=model.finished_at,
            approval_decision=(
                ApprovalDecision(model.approval_decision)
                if model.approval_decision is not None
                else None
            ),
            approval_decision_at=model.approval_decision_at,
            rejection_reason=model.rejection_reason,
            service_items=service_items,
            part_items=part_items,
        )

    async def list_all(self) -> list[ServiceOrder]:
        query = select(ServiceOrderModel).order_by(ServiceOrderModel.created_at.asc())
        result = await self.session.execute(query)
        return await self._hydrate_service_orders(result.scalars().all())

    async def update_status(
        self, service_order_id: UUID, status: ServiceOrderStatus
    ) -> None:
        query = select(ServiceOrderModel).where(ServiceOrderModel.id == service_order_id)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()

        if model:
            model.status = status.value
            model.updated_at = utcnow()
            await self.session.commit()

    async def set_started_at(self, service_order_id: UUID) -> None:
        result = await self.session.execute(
            select(ServiceOrderModel).where(ServiceOrderModel.id == service_order_id)
        )
        model = result.scalar_one_or_none()
        if model and model.started_at is None:
            model.started_at = utcnow()
            await self.session.commit()

    async def set_finished_at(self, service_order_id: UUID) -> None:
        result = await self.session.execute(
            select(ServiceOrderModel).where(ServiceOrderModel.id == service_order_id)
        )
        model = result.scalar_one_or_none()
        if model and model.finished_at is None:
            model.finished_at = utcnow()
            await self.session.commit()

    async def get_average_execution_time_seconds(self) -> float | None:
        result = await self.session.execute(
            select(
                func.avg(
                    func.extract(
                        "epoch",
                        ServiceOrderModel.finished_at - ServiceOrderModel.started_at,
                    )
                )
            ).where(
                ServiceOrderModel.started_at.is_not(None),
                ServiceOrderModel.finished_at.is_not(None),
            )
        )
        avg_seconds = result.scalar_one_or_none()
        return float(avg_seconds) if avg_seconds is not None else None

    async def list_active(self) -> list[ServiceOrder]:
        query = (
            select(ServiceOrderModel)
            .where(
                ServiceOrderModel.status.notin_(
                    [
                        ServiceOrderStatus.FINISHED.value,
                        ServiceOrderStatus.DELIVERED.value,
                    ]
                )
            )
            .order_by(
                ServiceOrderModel.created_at.asc(),
            )
        )
        result = await self.session.execute(query)
        return await self._hydrate_service_orders(result.scalars().all())

    async def _hydrate_service_orders(
        self,
        models: list[ServiceOrderModel],
    ) -> list[ServiceOrder]:
        service_orders = []
        for model in models:
            service_items_query = select(ServiceItemModel).where(
                ServiceItemModel.service_order_id == model.id
            )
            service_items_result = await self.session.execute(service_items_query)
            service_items_models = service_items_result.scalars().all()

            part_items_query = select(PartItemModel).where(
                PartItemModel.service_order_id == model.id
            )
            part_items_result = await self.session.execute(part_items_query)
            part_items_models = part_items_result.scalars().all()

            service_items = [
                ServiceItem(
                    id=item.id,
                    service_order_id=item.service_order_id,
                    description=item.description,
                    price=float(item.price),
                    created_at=item.created_at,
                )
                for item in service_items_models
            ]

            part_items = [
                PartItem(
                    id=item.id,
                    service_order_id=item.service_order_id,
                    name=item.name,
                    price=float(item.price),
                    quantity=item.quantity,
                    created_at=item.created_at,
                )
                for item in part_items_models
            ]

            service_orders.append(
                ServiceOrder(
                    id=model.id,
                    customer_id=model.customer_id,
                    vehicle_id=model.vehicle_id,
                    status=ServiceOrderStatus(model.status),
                    created_at=model.created_at,
                    updated_at=model.updated_at,
                    started_at=model.started_at,
                    finished_at=model.finished_at,
                    approval_decision=(
                        ApprovalDecision(model.approval_decision)
                        if model.approval_decision is not None
                        else None
                    ),
                    approval_decision_at=model.approval_decision_at,
                    rejection_reason=model.rejection_reason,
                    service_items=service_items,
                    part_items=part_items,
                )
            )

        return service_orders
