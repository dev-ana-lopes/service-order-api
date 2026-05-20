from typing import Annotated

from fastapi import APIRouter, Depends

from ....application.use_cases.metrics_use_case import GetAverageExecutionTimeUseCase
from ....domain.contracts.token_verifier import AuthenticatedPrincipal
from ....domain.repositories import ServiceOrderRepository
from ....presentation.dependencies.auth import require_admin_principal
from ....presentation.dependencies.db_dependencies import get_service_order_repository
from ....presentation.schemas.admin_schema import AverageExecutionTimeResponse

router = APIRouter(
    prefix="/metrics",
    tags=["metrics"],
)

ServiceOrderRepo = Annotated[
    ServiceOrderRepository, Depends(get_service_order_repository)
]
AdminPrincipal = Annotated[AuthenticatedPrincipal, Depends(require_admin_principal)]


@router.get("/average-execution-time")
async def get_average_execution_time(
    service_order_repo: ServiceOrderRepo,
    principal: AdminPrincipal,
) -> AverageExecutionTimeResponse:
    del principal
    use_case = GetAverageExecutionTimeUseCase(service_order_repo)
    avg = await use_case.execute()
    return AverageExecutionTimeResponse(average_execution_time_seconds=avg)
