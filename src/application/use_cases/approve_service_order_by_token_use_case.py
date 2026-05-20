from __future__ import annotations

import logging
from uuid import UUID

from ...domain.enums import ServiceOrderStatus
from ...domain.errors import ApprovalTokenMismatchError
from ...domain.services import ApprovalTokenService
from .apply_service_order_approval_decision_use_case import (
    ApplyServiceOrderApprovalDecisionUseCase,
)

logger = logging.getLogger(__name__)


class ApproveServiceOrderByTokenUseCase:
    def __init__(
        self,
        approval_token_service: ApprovalTokenService,
        apply_service_order_approval_use_case: ApplyServiceOrderApprovalDecisionUseCase,
    ):
        self.approval_token_service = approval_token_service
        self.apply_service_order_approval_use_case = (
            apply_service_order_approval_use_case
        )

    async def execute(self, service_order_id: UUID, token: str) -> ServiceOrderStatus:
        payload = self.approval_token_service.verify_token(token)
        if payload.service_order_id != service_order_id:
            raise ApprovalTokenMismatchError(service_order_id, payload.service_order_id)

        logger.info(
            "Approval token accepted for service order %s with decision=%s",
            service_order_id,
            "approve" if payload.approved else "reject",
        )
        return await self.apply_service_order_approval_use_case.execute(
            service_order_id, payload.approved
        )
