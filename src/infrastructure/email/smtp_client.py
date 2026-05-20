import logging
import smtplib
import ssl
from asyncio import to_thread
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.parse import quote

from ...domain.services import ApprovalRequestEmailMessage, EmailSender
from ..config.settings import Settings

logger = logging.getLogger(__name__)


class SmtpEmailSender(EmailSender):
    def __init__(self, settings: Settings):
        self.settings = settings

    def _from_email(self) -> str:
        return self.settings.SMTP_FROM_EMAIL or "no-reply@localhost"

    def _build_message(
        self,
        to_email: str,
        subject: str,
        body: str,
    ) -> MIMEMultipart:
        message = MIMEMultipart()
        message["From"] = self._from_email()
        message["To"] = to_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain", "utf-8"))
        return message

    def _approval_action_url(self, service_order_id: str, token: str) -> str:
        base_url = self.settings.APP_BASE_URL.rstrip("/")
        encoded_token = quote(token, safe="")
        return (
            f"{base_url}/public/service-orders/{service_order_id}"
            f"/approval?token={encoded_token}"
        )

    def _send_message(self, message: MIMEMultipart) -> None:
        with smtplib.SMTP(
            self.settings.SMTP_HOST,
            self.settings.SMTP_PORT,
            timeout=self.settings.SMTP_TIMEOUT_SECONDS,
        ) as server:
            server.ehlo()
            if self.settings.SMTP_USE_TLS:
                server.starttls(context=ssl.create_default_context())
                server.ehlo()
            if self.settings.SMTP_USE_AUTH and self.settings.SMTP_USERNAME:
                server.login(
                    self.settings.SMTP_USERNAME,
                    self.settings.SMTP_PASSWORD,
                )
            server.send_message(message)

    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
    ) -> None:
        message = self._build_message(to_email, subject, body)
        logger.info("Sending email to %s with subject '%s'", to_email, subject)
        await to_thread(self._send_message, message)

    async def send_status_changed(
        self, customer_email: str, service_order_id: str, new_status: str
    ) -> None:
        subject = "Service Order Status Updated"
        body = f"""
Your service order status has been updated.

Service Order ID: {service_order_id}
New Status: {new_status}

Please contact us if you have any questions.
        """
        await self.send_email(customer_email, subject, body)

    async def send_approval_request(
        self,
        message: ApprovalRequestEmailMessage,
    ) -> None:
        subject = "Aprovacao de orcamento da ordem de servico"
        summary_block = "\n".join(message.summary_lines)
        approve_url = self._approval_action_url(
            message.service_order_id,
            message.approve_token,
        )
        reject_url = self._approval_action_url(
            message.service_order_id,
            message.reject_token,
        )
        body = f"""
Sua ordem de servico aguarda aprovacao.

OS: {message.service_order_id}
Valor total do orcamento: R$ {message.total:.2f}

Resumo do orcamento:
{summary_block}

Aprovar:
{approve_url}

Rejeitar:
{reject_url}

Se voce nao reconhece esta solicitacao, entre em contato com a oficina.
        """
        await self.send_email(message.customer_email, subject, body)
