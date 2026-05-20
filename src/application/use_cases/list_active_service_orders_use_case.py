from ...domain.enums import ServiceOrderStatus
from ...domain.repositories import ServiceOrderRepository


class ListActiveServiceOrdersUseCase:
    def __init__(self, service_order_repo: ServiceOrderRepository):
        self.service_order_repo = service_order_repo

    async def execute(self) -> list:
        service_orders = await self.service_order_repo.list_active()

        priority_map = {
            ServiceOrderStatus.IN_PROGRESS: 0,
            ServiceOrderStatus.WAITING_APPROVAL: 1,
            ServiceOrderStatus.DIAGNOSIS: 2,
            ServiceOrderStatus.RECEIVED: 3,
        }

        service_orders.sort(
            key=lambda so: (priority_map.get(so.status, 999), so.created_at)
        )

        return service_orders
