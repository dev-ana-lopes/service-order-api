from __future__ import annotations

import logging

from ...domain.entities import ServiceOrder
from ...domain.services import (
    ApprovalRequestEmailMessage,
    ApprovalTokenService,
    EmailSender,
)

logger = logging.getLogger(__name__)


class SendApprovalRequestEmailUseCase:
    def __init__(
        self,
        email_sender: EmailSender,
        approval_token_service: ApprovalTokenService,
    ):
        self.email_sender = email_sender
        self.approval_token_service = approval_token_service

    async def execute(self, customer_email: str, service_order: ServiceOrder) -> None:
        approve_token = self.approval_token_service.generate_token(
            service_order.id, approved=True
        )
        reject_token = self.approval_token_service.generate_token(
            service_order.id, approved=False
        )
        message = ApprovalRequestEmailMessage(
            customer_email=customer_email,
            service_order_id=str(service_order.id),
            total=service_order.budget_total,
            summary_lines=self._build_summary_lines(service_order),
            approve_token=approve_token,
            reject_token=reject_token,
        )
        logger.info(
            "Sending approval request email for service order %s to %s",
            service_order.id,
            customer_email,
        )
        await self.email_sender.send_approval_request(message)

    def _build_summary_lines(self, service_order: ServiceOrder) -> tuple[str, ...]:
        lines: list[str] = []
        for item in service_order.service_items:
            lines.append(f"Servico: {item.description} - R$ {item.price:.2f}")
        for item in service_order.part_items:
            lines.append(
                f"Peca: {item.name} x{item.quantity} - "
                f"R$ {item.price * item.quantity:.2f}"
            )
        if not lines:
            lines.append("Sem itens detalhados no orcamento.")
        return tuple(lines)
