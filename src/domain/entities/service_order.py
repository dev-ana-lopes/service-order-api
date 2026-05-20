from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from ..enums import ApprovalDecision, ServiceOrderStatus
from ..errors import InvalidServiceOrderTransitionError
from ..time import utcnow
from .part_item import PartItem
from .service_item import ServiceItem


@dataclass
class ServiceOrder:
    id: UUID
    customer_id: UUID
    vehicle_id: UUID
    status: ServiceOrderStatus
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    approval_decision: ApprovalDecision | None = None
    approval_decision_at: datetime | None = None
    rejection_reason: str | None = None
    service_items: list[ServiceItem] = field(default_factory=list)
    part_items: list[PartItem] = field(default_factory=list)

    _ALLOWED_TRANSITIONS = {
        ServiceOrderStatus.RECEIVED: {
            ServiceOrderStatus.DIAGNOSIS,
            ServiceOrderStatus.WAITING_APPROVAL,
        },
        ServiceOrderStatus.DIAGNOSIS: {
            ServiceOrderStatus.WAITING_APPROVAL,
            ServiceOrderStatus.IN_PROGRESS,
        },
        ServiceOrderStatus.WAITING_APPROVAL: {
            ServiceOrderStatus.IN_PROGRESS,
            ServiceOrderStatus.DIAGNOSIS,
        },
        ServiceOrderStatus.IN_PROGRESS: {
            ServiceOrderStatus.FINISHED,
        },
        ServiceOrderStatus.FINISHED: {
            ServiceOrderStatus.DELIVERED,
        },
        ServiceOrderStatus.DELIVERED: set(),
    }

    @property
    def budget_total(self) -> float:
        services_total = sum(item.price for item in self.service_items)
        parts_total = sum(item.price * item.quantity for item in self.part_items)
        return services_total + parts_total

    def can_transition_to(self, target_status: ServiceOrderStatus) -> bool:
        if target_status == self.status:
            return True
        return target_status in self._ALLOWED_TRANSITIONS[self.status]

    @property
    def is_active(self) -> bool:
        return self.status not in {
            ServiceOrderStatus.FINISHED,
            ServiceOrderStatus.DELIVERED,
        }

    def transition_to(
        self,
        target_status: ServiceOrderStatus,
        changed_at: datetime | None = None,
    ) -> None:
        if not self.can_transition_to(target_status):
            raise InvalidServiceOrderTransitionError(self.status, target_status)
        moment = changed_at or utcnow()
        self.status = target_status
        self.updated_at = moment
        if target_status == ServiceOrderStatus.IN_PROGRESS and self.started_at is None:
            self.started_at = moment
        if target_status == ServiceOrderStatus.FINISHED and self.finished_at is None:
            self.finished_at = moment

    def apply_budget_decision(
        self,
        approved: bool,
        changed_at: datetime | None = None,
        rejection_reason: str | None = None,
    ) -> ServiceOrderStatus:
        target_status = (
            ServiceOrderStatus.IN_PROGRESS if approved else ServiceOrderStatus.DIAGNOSIS
        )
        moment = changed_at or utcnow()
        self.approval_decision = (
            ApprovalDecision.APPROVED if approved else ApprovalDecision.REJECTED
        )
        self.approval_decision_at = moment
        self.rejection_reason = rejection_reason if not approved else None
        self.transition_to(target_status, changed_at=moment)
        return target_status
