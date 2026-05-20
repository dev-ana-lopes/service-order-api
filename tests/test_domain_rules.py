from datetime import timedelta
from uuid import uuid4

import pytest

from src.application.use_cases.list_active_service_orders_use_case import (
    ListActiveServiceOrdersUseCase,
)
from src.application.use_cases.metrics_use_case import GetAverageExecutionTimeUseCase
from src.domain.entities import ServiceOrder
from src.domain.enums import ApprovalDecision, ServiceOrderStatus
from src.domain.errors import InvalidServiceOrderTransitionError
from src.domain.time import utcnow
from tests.support import MockServiceOrderRepository


def _service_order(
    status: ServiceOrderStatus, created_offset_minutes: int = 0
) -> ServiceOrder:
    created_at = utcnow() - timedelta(minutes=created_offset_minutes)
    return ServiceOrder(
        id=uuid4(),
        customer_id=uuid4(),
        vehicle_id=uuid4(),
        status=status,
        created_at=created_at,
        updated_at=created_at,
    )


def test_service_order_budget_total_and_active_flag():
    order = _service_order(ServiceOrderStatus.RECEIVED)
    order.service_items = []
    order.part_items = []

    assert order.budget_total == 0
    assert order.is_active is True

    order.transition_to(ServiceOrderStatus.DIAGNOSIS, changed_at=utcnow())
    order.transition_to(ServiceOrderStatus.WAITING_APPROVAL, changed_at=utcnow())
    order.transition_to(ServiceOrderStatus.IN_PROGRESS, changed_at=utcnow())
    order.transition_to(ServiceOrderStatus.FINISHED, changed_at=utcnow())

    assert order.finished_at is not None
    assert order.is_active is False


def test_rejecting_budget_returns_order_to_diagnosis_and_records_reason():
    order = _service_order(ServiceOrderStatus.WAITING_APPROVAL)

    status = order.apply_budget_decision(
        approved=False,
        changed_at=utcnow(),
        rejection_reason="Cliente pediu revisao do orcamento",
    )

    assert status == ServiceOrderStatus.DIAGNOSIS
    assert order.approval_decision == ApprovalDecision.REJECTED
    assert order.rejection_reason == "Cliente pediu revisao do orcamento"


def test_service_order_rejects_invalid_transition():
    order = _service_order(ServiceOrderStatus.WAITING_APPROVAL)

    with pytest.raises(InvalidServiceOrderTransitionError):
        order.transition_to(ServiceOrderStatus.FINISHED, changed_at=utcnow())


@pytest.mark.asyncio
async def test_list_active_service_orders_applies_priority_and_age_rules():
    repo = MockServiceOrderRepository()
    received = _service_order(ServiceOrderStatus.RECEIVED, created_offset_minutes=5)
    diagnosis = _service_order(ServiceOrderStatus.DIAGNOSIS, created_offset_minutes=4)
    waiting_old = _service_order(
        ServiceOrderStatus.WAITING_APPROVAL, created_offset_minutes=30
    )
    waiting_new = _service_order(
        ServiceOrderStatus.WAITING_APPROVAL, created_offset_minutes=10
    )
    in_progress = _service_order(
        ServiceOrderStatus.IN_PROGRESS, created_offset_minutes=1
    )
    finished = _service_order(ServiceOrderStatus.FINISHED, created_offset_minutes=100)

    for order in [received, diagnosis, waiting_new, waiting_old, in_progress, finished]:
        await repo.save(order)

    use_case = ListActiveServiceOrdersUseCase(repo)
    orders = await use_case.execute()

    assert [order.id for order in orders] == [
        in_progress.id,
        waiting_old.id,
        waiting_new.id,
        diagnosis.id,
        received.id,
    ]


@pytest.mark.asyncio
async def test_average_execution_time_use_case_returns_seconds():
    repo = MockServiceOrderRepository()
    first = _service_order(ServiceOrderStatus.FINISHED)
    second = _service_order(ServiceOrderStatus.FINISHED)
    first.started_at = utcnow() - timedelta(minutes=20)
    first.finished_at = utcnow() - timedelta(minutes=10)
    second.started_at = utcnow() - timedelta(minutes=50)
    second.finished_at = utcnow() - timedelta(minutes=20)
    await repo.save(first)
    await repo.save(second)

    use_case = GetAverageExecutionTimeUseCase(repo)
    average_seconds = await use_case.execute()

    assert average_seconds == pytest.approx(1200.0)
