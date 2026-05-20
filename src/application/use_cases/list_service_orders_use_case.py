from ...domain.entities import ServiceOrder
from ...domain.repositories import ServiceOrderRepository


class ListServiceOrdersUseCase:
    def __init__(self, service_order_repo: ServiceOrderRepository):
        self.service_order_repo = service_order_repo

    async def execute(self) -> list[ServiceOrder]:
        return await self.service_order_repo.list_all()
