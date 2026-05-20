from ...domain.entities import ServiceOrder
from ..schemas.service_order_schema import (
    PartItemResponse,
    ServiceItemResponse,
    ServiceOrderResponse,
)


def serialize_service_order(service_order: ServiceOrder) -> ServiceOrderResponse:
    return ServiceOrderResponse(
        id=str(service_order.id),
        customer_id=str(service_order.customer_id),
        vehicle_id=str(service_order.vehicle_id),
        status=service_order.status.value,
        created_at=service_order.created_at.isoformat(),
        updated_at=service_order.updated_at.isoformat(),
        started_at=(
            service_order.started_at.isoformat()
            if service_order.started_at is not None
            else None
        ),
        finished_at=(
            service_order.finished_at.isoformat()
            if service_order.finished_at is not None
            else None
        ),
        budget_total=service_order.budget_total,
        approval_decision=(
            service_order.approval_decision.value
            if service_order.approval_decision is not None
            else None
        ),
        approval_decision_at=(
            service_order.approval_decision_at.isoformat()
            if service_order.approval_decision_at is not None
            else None
        ),
        rejection_reason=service_order.rejection_reason,
        service_items=[
            ServiceItemResponse(
                id=str(item.id),
                description=item.description,
                price=item.price,
            )
            for item in service_order.service_items
        ],
        part_items=[
            PartItemResponse(
                id=str(item.id),
                name=item.name,
                price=item.price,
                quantity=item.quantity,
            )
            for item in service_order.part_items
        ],
    )
