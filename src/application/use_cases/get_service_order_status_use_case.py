from uuid import UUID

from ...domain.repositories import ServiceOrderRepository


class GetServiceOrderStatusUseCase:
    def __init__(self, service_order_repo: ServiceOrderRepository):
        self.service_order_repo = service_order_repo

    async def execute(self, service_order_id: UUID) -> str | None:
        service_order = await self.service_order_repo.get_by_id(service_order_id)
        if service_order is None:
            return None
        return service_order.status.value
