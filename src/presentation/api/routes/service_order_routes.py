from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from ....application.dto.create_service_order_dto import CreateServiceOrderDTO
from ....application.use_cases.approve_service_order_use_case import (
    ApproveServiceOrderUseCase,
)
from ....application.use_cases.create_service_order_use_case import (
    CreateServiceOrderUseCase,
)
from ....application.use_cases.get_service_order_details_use_case import (
    GetServiceOrderDetailsUseCase,
)
from ....application.use_cases.get_service_order_status_use_case import (
    GetServiceOrderStatusUseCase,
)
from ....application.use_cases.list_active_service_orders_use_case import (
    ListActiveServiceOrdersUseCase,
)
from ....application.use_cases.list_service_orders_use_case import (
    ListServiceOrdersUseCase,
)
from ....application.use_cases.update_service_order_status_use_case import (
    UpdateServiceOrderStatusUseCase,
)
from ....domain.contracts.token_verifier import AuthenticatedPrincipal
from ....domain.entities import ServiceOrder
from ....domain.errors import (
    ApprovalActionAlreadyProcessedError,
    InvalidServiceOrderTransitionError,
    ServiceOrderNotFoundError,
)
from ....domain.repositories import (
    CatalogServiceRepository,
    CustomerRepository,
    InventoryPartRepository,
    PartItemRepository,
    ServiceItemRepository,
    ServiceOrderRepository,
    VehicleRepository,
)
from ....domain.services import ApprovalTokenService, EmailSender
from ....infrastructure.observability.metrics import (
    SERVICE_ORDER_FAILURES,
    SERVICE_ORDER_STATUS,
    SERVICE_ORDERS_CREATED,
)
from ....presentation.api.serializers import serialize_service_order
from ....presentation.dependencies.auth import require_customer_or_admin_principal
from ....presentation.dependencies.db_dependencies import (
    get_approval_token_service,
    get_catalog_service_repository,
    get_customer_repository,
    get_email_sender,
    get_inventory_part_repository,
    get_part_item_repository,
    get_service_item_repository,
    get_service_order_repository,
    get_vehicle_repository,
)
from ....presentation.schemas.service_order_schema import (
    ApproveServiceOrderRequest,
    ApproveServiceOrderResponse,
    CreateServiceOrderRequest,
    CreateServiceOrderResponse,
    ServiceOrderResponse,
    ServiceOrderStatusResponse,
    UpdateServiceOrderStatusRequest,
)

router = APIRouter(
    prefix="/service-orders",
    tags=["service-orders"],
)

Principal = Annotated[
    AuthenticatedPrincipal,
    Depends(require_customer_or_admin_principal),
]
CustomerRepo = Annotated[CustomerRepository, Depends(get_customer_repository)]
CatalogServiceRepo = Annotated[
    CatalogServiceRepository,
    Depends(get_catalog_service_repository),
]
VehicleRepo = Annotated[VehicleRepository, Depends(get_vehicle_repository)]
ServiceOrderRepo = Annotated[
    ServiceOrderRepository, Depends(get_service_order_repository)
]
ServiceItemRepo = Annotated[ServiceItemRepository, Depends(get_service_item_repository)]
PartItemRepo = Annotated[PartItemRepository, Depends(get_part_item_repository)]
InventoryPartRepo = Annotated[
    InventoryPartRepository,
    Depends(get_inventory_part_repository),
]
EmailGateway = Annotated[EmailSender, Depends(get_email_sender)]
ApprovalTokenSvc = Annotated[ApprovalTokenService, Depends(get_approval_token_service)]


async def _load_service_order_or_404(
    service_order_repo: ServiceOrderRepo,
    service_order_id: UUID,
) -> ServiceOrder:
    use_case = GetServiceOrderDetailsUseCase(service_order_repo)
    service_order = await use_case.execute(service_order_id)
    if service_order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service order not found",
        )
    return service_order


async def _ensure_customer_access(
    principal: AuthenticatedPrincipal,
    service_order_repo: ServiceOrderRepo,
    service_order_id: UUID,
) -> ServiceOrder:
    service_order = await _load_service_order_or_404(service_order_repo, service_order_id)
    if principal.is_customer and str(service_order.customer_id) != str(principal.customer_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer token cannot access another customer's service order",
        )
    return service_order


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_service_order(
    request: CreateServiceOrderRequest,
    principal: Principal,
    customer_repo: CustomerRepo,
    vehicle_repo: VehicleRepo,
    service_order_repo: ServiceOrderRepo,
    service_item_repo: ServiceItemRepo,
    part_item_repo: PartItemRepo,
    catalog_service_repo: CatalogServiceRepo,
    inventory_part_repo: InventoryPartRepo,
    email_sender: EmailGateway,
    approval_token_service: ApprovalTokenSvc,
) -> CreateServiceOrderResponse:
    if not request.service_ids and not request.services:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Either services or service_ids must be provided",
        )

    request_customer_id = request.customer_id
    if principal.is_customer:
        if request_customer_id and request_customer_id != str(principal.customer_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Customer token cannot create service orders for another customer",
            )
        request_customer_id = str(principal.customer_id)

    dto = CreateServiceOrderDTO(
        customer_id=request_customer_id,
        vehicle_id=request.vehicle_id,
        customer_name=request.customer_name,
        customer_cpf_cnpj=request.customer_cpf_cnpj,
        customer_email=request.customer_email,
        customer_phone=request.customer_phone,
        vehicle_brand=request.vehicle_brand,
        vehicle_model=request.vehicle_model,
        vehicle_year=request.vehicle_year,
        vehicle_plate=request.vehicle_plate,
        services=(
            [
                {"description": s.description, "price": s.price}
                for s in (request.services or [])
            ]
            if request.services is not None
            else None
        ),
        parts=(
            [
                {"name": p.name, "price": p.price, "quantity": p.quantity}
                for p in (request.parts or [])
            ]
            if request.parts is not None
            else None
        ),
        service_ids=request.service_ids,
        part_refs=(
            [
                {"part_id": p.part_id, "quantity": p.quantity}
                for p in (request.part_refs or [])
            ]
            if request.part_refs is not None
            else None
        ),
    )

    use_case = CreateServiceOrderUseCase(
        customer_repo,
        vehicle_repo,
        service_order_repo,
        service_item_repo,
        part_item_repo,
        catalog_service_repo,
        inventory_part_repo,
        email_sender,
        approval_token_service,
    )

    try:
        service_order_id = await use_case.execute(dto)
    except LookupError as e:
        SERVICE_ORDER_FAILURES.labels(stage="lookup").inc()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except ValueError as e:
        SERVICE_ORDER_FAILURES.labels(stage="validation").inc()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    SERVICE_ORDERS_CREATED.inc()
    SERVICE_ORDER_STATUS.labels(status="WAITING_APPROVAL").inc()
    return CreateServiceOrderResponse(service_order_id=service_order_id)


@router.get("/active")
async def list_active_service_orders(
    principal: Principal,
    service_order_repo: ServiceOrderRepo,
) -> list[ServiceOrderResponse]:
    use_case = ListActiveServiceOrdersUseCase(service_order_repo)
    service_orders = await use_case.execute()
    if principal.is_customer:
        service_orders = [
            service_order
            for service_order in service_orders
            if str(service_order.customer_id) == str(principal.customer_id)
        ]
    return [serialize_service_order(service_order) for service_order in service_orders]


@router.get("/{id}/status")
async def get_service_order_status(
    id: UUID,
    principal: Principal,
    service_order_repo: ServiceOrderRepo,
) -> ServiceOrderStatusResponse:
    service_order = await _ensure_customer_access(principal, service_order_repo, id)
    use_case = GetServiceOrderStatusUseCase(service_order_repo)
    order_status = await use_case.execute(id)

    if order_status is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service order not found",
        )

    return ServiceOrderStatusResponse(
        status=order_status,
        approval_decision=(
            service_order.approval_decision.value
            if service_order.approval_decision is not None
            else None
        ),
        rejection_reason=service_order.rejection_reason,
    )


@router.get("/{id}")
async def get_service_order(
    id: UUID,
    principal: Principal,
    service_order_repo: ServiceOrderRepo,
) -> ServiceOrderResponse:
    service_order = await _ensure_customer_access(principal, service_order_repo, id)
    return serialize_service_order(service_order)


@router.get("")
async def list_service_orders(
    principal: Principal,
    service_order_repo: ServiceOrderRepo,
) -> list[ServiceOrderResponse]:
    use_case = ListServiceOrdersUseCase(service_order_repo)
    service_orders = await use_case.execute()
    if principal.is_customer:
        service_orders = [
            service_order
            for service_order in service_orders
            if str(service_order.customer_id) == str(principal.customer_id)
        ]
    return [serialize_service_order(service_order) for service_order in service_orders]


@router.post("/{id}/approval")
async def approve_service_order(
    id: UUID,
    request: ApproveServiceOrderRequest,
    principal: Principal,
    customer_repo: CustomerRepo,
    service_order_repo: ServiceOrderRepo,
    email_sender: EmailGateway,
) -> ApproveServiceOrderResponse:
    await _ensure_customer_access(principal, service_order_repo, id)
    use_case = ApproveServiceOrderUseCase(
        service_order_repo, customer_repo, email_sender
    )
    try:
        updated_status = await use_case.execute(
            id,
            request.approved,
            request.rejection_reason,
        )
    except ServiceOrderNotFoundError as exc:
        SERVICE_ORDER_FAILURES.labels(stage="approval_not_found").inc()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service order not found",
        ) from exc
    except ApprovalActionAlreadyProcessedError as exc:
        SERVICE_ORDER_FAILURES.labels(stage="approval_conflict").inc()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    SERVICE_ORDER_STATUS.labels(status=updated_status.value).inc()
    return ApproveServiceOrderResponse(
        status=updated_status.value,
        decision="APPROVED" if request.approved else "REJECTED",
        rejection_reason=request.rejection_reason if not request.approved else None,
    )


@router.patch("/{id}/status")
async def update_service_order_status(
    id: UUID,
    request: UpdateServiceOrderStatusRequest,
    principal: Principal,
    customer_repo: CustomerRepo,
    service_order_repo: ServiceOrderRepo,
    email_sender: EmailGateway,
) -> ApproveServiceOrderResponse:
    if principal.is_customer:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer token cannot update service order lifecycle status",
        )

    use_case = UpdateServiceOrderStatusUseCase(
        service_order_repo,
        customer_repo,
        email_sender,
    )
    try:
        updated_status = await use_case.execute(id, request.status)
    except ServiceOrderNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service order not found",
        ) from exc
    except InvalidServiceOrderTransitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    SERVICE_ORDER_STATUS.labels(status=updated_status.value).inc()
    return ApproveServiceOrderResponse(
        status=updated_status.value,
        decision="STATUS_UPDATED",
    )
