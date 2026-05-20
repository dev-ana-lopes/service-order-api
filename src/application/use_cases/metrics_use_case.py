from ...domain.repositories import ServiceOrderRepository


class GetAverageExecutionTimeUseCase:
    def __init__(self, service_order_repo: ServiceOrderRepository):
        self.service_order_repo = service_order_repo

    async def execute(self) -> float | None:
        return await self.service_order_repo.get_average_execution_time_seconds()
