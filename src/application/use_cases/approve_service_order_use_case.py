from uuid import UUID

from ...domain.enums import ServiceOrderStatus
from ...domain.repositories import CustomerRepository, ServiceOrderRepository
from ...domain.services import EmailSender
from .apply_service_order_approval_decision_use_case import (
    ApplyServiceOrderApprovalDecisionUseCase,
)


class ApproveServiceOrderUseCase:
    def __init__(
        self,
        service_order_repo: ServiceOrderRepository,
        customer_repo: CustomerRepository,
        email_sender: EmailSender,
    ):
        self.apply_service_order_approval_use_case = (
            ApplyServiceOrderApprovalDecisionUseCase(
                service_order_repo,
                customer_repo,
                email_sender,
            )
        )

    async def execute(
        self,
        service_order_id: UUID,
        approved: bool,
        rejection_reason: str | None = None,
    ) -> ServiceOrderStatus:
        return await self.apply_service_order_approval_use_case.execute(
            service_order_id, approved, rejection_reason
        )
