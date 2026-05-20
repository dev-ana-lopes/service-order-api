import logging

from ...domain.services import ApprovalRequestEmailMessage, EmailSender

logger = logging.getLogger(__name__)


class NoopEmailSender(EmailSender):
    async def send_email(self, to_email: str, subject: str, body: str) -> None:
        logger.info(
            "NOOP email provider enabled; skipping generic email",
            extra={"to_email": to_email, "subject": subject},
        )

    async def send_status_changed(
        self,
        customer_email: str,
        service_order_id: str,
        new_status: str,
    ) -> None:
        logger.info(
            "NOOP email provider enabled; skipping status notification",
            extra={
                "to_email": customer_email,
                "service_order_id": service_order_id,
                "new_status": new_status,
            },
        )

    async def send_approval_request(
        self,
        message: ApprovalRequestEmailMessage,
    ) -> None:
        logger.info(
            "NOOP email provider enabled; skipping approval request email",
            extra={
                "to_email": message.customer_email,
                "service_order_id": message.service_order_id,
                "total": message.total,
            },
        )
