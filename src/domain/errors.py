from __future__ import annotations

from uuid import UUID

from .enums import ServiceOrderStatus


class DomainError(Exception):
    """Base class for domain and workflow errors."""


class ServiceOrderNotFoundError(DomainError):
    def __init__(self, service_order_id: UUID):
        self.service_order_id = service_order_id
        super().__init__(f"Service order {service_order_id} not found")


class InvalidServiceOrderTransitionError(DomainError):
    def __init__(
        self,
        current_status: ServiceOrderStatus,
        target_status: ServiceOrderStatus,
    ):
        self.current_status = current_status
        self.target_status = target_status
        super().__init__(
            "Cannot transition service order from "
            f"{current_status.value} to {target_status.value}"
        )


class ApprovalActionAlreadyProcessedError(DomainError):
    def __init__(self, current_status: ServiceOrderStatus):
        self.current_status = current_status
        super().__init__(
            "Approval action is no longer available because the service order "
            f"is currently {current_status.value}"
        )


class ApprovalTokenError(DomainError):
    """Base class for approval-token validation errors."""


class InvalidApprovalTokenError(ApprovalTokenError):
    pass


class ExpiredApprovalTokenError(ApprovalTokenError):
    pass


class ApprovalTokenMismatchError(ApprovalTokenError):
    def __init__(self, expected_service_order_id: UUID, token_service_order_id: UUID):
        self.expected_service_order_id = expected_service_order_id
        self.token_service_order_id = token_service_order_id
        super().__init__("Approval token does not match the requested service order")
