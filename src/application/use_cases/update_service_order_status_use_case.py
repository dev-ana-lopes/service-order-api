import logging
from uuid import UUID

from ...domain.enums import ServiceOrderStatus
from ...domain.errors import ServiceOrderNotFoundError
from ...domain.repositories import CustomerRepository, ServiceOrderRepository
from ...domain.services import ApprovalTokenService, EmailSender
from ...domain.time import utcnow
from .send_approval_request_email_use_case import SendApprovalRequestEmailUseCase

logger = logging.getLogger(__name__)


class UpdateServiceOrderStatusUseCase:
    def __init__(
        self,
        service_order_repo: ServiceOrderRepository,
        customer_repo: CustomerRepository,
        email_sender: EmailSender,
        approval_token_service: ApprovalTokenService,
    ):
        self.service_order_repo = service_order_repo
        self.customer_repo = customer_repo
        self.email_sender = email_sender
        self.send_approval_request_email_use_case = SendApprovalRequestEmailUseCase(
            email_sender,
            approval_token_service,
        )

    async def execute(self, service_order_id: UUID, status: str) -> ServiceOrderStatus:
        try:
            status_enum = ServiceOrderStatus(status)
        except ValueError as exc:
            raise ValueError("Invalid service order status") from exc

        service_order = await self.service_order_repo.get_by_id(service_order_id)

        if service_order is None:
            raise ServiceOrderNotFoundError(service_order_id)

        service_order.transition_to(status_enum, changed_at=utcnow())
        await self.service_order_repo.update(service_order)

        customer = await self.customer_repo.get_by_id(service_order.customer_id)
        if customer is not None:
            try:
                if status_enum == ServiceOrderStatus.WAITING_APPROVAL:
                    await self.send_approval_request_email_use_case.execute(
                        customer.email,
                        service_order,
                    )
                else:
                    await self.email_sender.send_status_changed(
                        customer.email,
                        str(service_order_id),
                        status_enum.value,
                    )
            except Exception:
                logger.exception(
                    "Failed to send notification for service order %s",
                    service_order_id,
                )

        return status_enum
