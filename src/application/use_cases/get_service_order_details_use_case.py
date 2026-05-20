from uuid import UUID

from ...domain.entities import ServiceOrder
from ...domain.repositories import ServiceOrderRepository


class GetServiceOrderDetailsUseCase:
    def __init__(self, service_order_repo: ServiceOrderRepository):
        self.service_order_repo = service_order_repo

    async def execute(self, service_order_id: UUID) -> ServiceOrder | None:
        return await self.service_order_repo.get_by_id(service_order_id)
