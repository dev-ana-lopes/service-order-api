from __future__ import annotations

from email import message_from_bytes
from email.policy import default

import pytest

from src.domain.services import ApprovalRequestEmailMessage
from src.infrastructure.config.settings import Settings
from src.infrastructure.email.noop_client import NoopEmailSender
from src.infrastructure.email.smtp_client import SmtpEmailSender


class _FakeSmtp:
    def __init__(self, host, port, timeout=None):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.ehlo_calls = 0
        self.starttls_called = False
        self.starttls_context = None
        self.login_called = False
        self.login_args = None
        self.sent_messages = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def ehlo(self):
        self.ehlo_calls += 1

    def starttls(self, context=None):
        self.starttls_called = True
        self.starttls_context = context

    def login(self, user, password):
        self.login_called = True
        self.login_args = (user, password)

    def send_message(self, message):
        self.sent_messages.append(message)


def _build_settings(**overrides) -> Settings:
    base = {
        "DATABASE_URL": "postgresql+asyncpg://user:pass@localhost:5432/db",
        "SMTP_HOST": "mailhog",
        "SMTP_PORT": 1025,
        "SMTP_FROM_EMAIL": "billing@example.com",
        "SMTP_USE_TLS": False,
        "SMTP_USE_AUTH": False,
        "JWT_SECRET": "test",
    }
    base.update(overrides)
    return Settings(**base)


def _install_fake_smtp(monkeypatch):
    created = {}

    def fake_smtp(host, port, timeout=None):
        created["client"] = _FakeSmtp(host, port, timeout=timeout)
        return created["client"]

    import src.infrastructure.email.smtp_client as smtp_client_module

    monkeypatch.setattr(smtp_client_module.smtplib, "SMTP", fake_smtp)
    return created


@pytest.mark.asyncio
async def test_smtp_sender_can_skip_tls_and_auth(monkeypatch):
    created = _install_fake_smtp(monkeypatch)
    settings = _build_settings(SMTP_FROM_EMAIL="")

    sender = SmtpEmailSender(settings)
    await sender.send_email("to@example.com", "Subject", "Body")

    client = created["client"]
    assert client.host == "mailhog"
    assert client.port == 1025
    assert client.timeout == 10
    assert client.ehlo_calls == 1
    assert client.starttls_called is False
    assert client.login_called is False
    assert len(client.sent_messages) == 1
    message = client.sent_messages[0]
    assert message["From"] == "no-reply@localhost"
    assert message["To"] == "to@example.com"
    assert message["Subject"] == "Subject"
    parsed = message_from_bytes(message.as_bytes(), policy=default)
    assert parsed.get_body(preferencelist=("plain",)).get_content_charset() == "utf-8"
    assert "Body" in parsed.get_body(preferencelist=("plain",)).get_content()


@pytest.mark.asyncio
async def test_smtp_sender_uses_tls_when_enabled(monkeypatch):
    created = _install_fake_smtp(monkeypatch)
    settings = _build_settings(SMTP_USE_TLS=True)

    sender = SmtpEmailSender(settings)
    await sender.send_email("to@example.com", "Subject", "Body")

    client = created["client"]
    assert client.ehlo_calls == 2
    assert client.starttls_called is True
    assert client.starttls_context is not None
    assert client.login_called is False
    assert len(client.sent_messages) == 1
    assert client.sent_messages[0]["From"] == "billing@example.com"


@pytest.mark.asyncio
async def test_smtp_sender_builds_approval_request_email(monkeypatch):
    created = _install_fake_smtp(monkeypatch)
    settings = _build_settings(APP_BASE_URL="https://api.example.com")
    sender = SmtpEmailSender(settings)
    message = ApprovalRequestEmailMessage(
        customer_email="customer@example.com",
        service_order_id="so-123",
        total=150.5,
        summary_lines=("Servico: Revisao - R$ 100.00", "Peca: Filtro x1 - R$ 50.50"),
        approve_token="approve-token",
        reject_token="reject-token",
    )

    await sender.send_approval_request(message)

    parsed = message_from_bytes(
        created["client"].sent_messages[0].as_bytes(),
        policy=default,
    )
    body = parsed.get_body(preferencelist=("plain",)).get_content()
    assert "OS: so-123" in body
    assert "Valor total do orcamento: R$ 150.50" in body
    assert "Servico: Revisao - R$ 100.00" in body
    assert "Peca: Filtro x1 - R$ 50.50" in body
    assert (
        "https://api.example.com/public/service-orders/so-123/"
        "approval?token=approve-token" in body
    )
    assert (
        "https://api.example.com/public/service-orders/so-123/"
        "approval?token=reject-token" in body
    )


@pytest.mark.asyncio
async def test_noop_email_sender_accepts_runtime_calls():
    sender = NoopEmailSender()
    message = ApprovalRequestEmailMessage(
        customer_email="customer@example.com",
        service_order_id="so-123",
        total=150.5,
        summary_lines=("Servico: Revisao - R$ 100.00",),
        approve_token="approve-token",
        reject_token="reject-token",
    )

    await sender.send_email("customer@example.com", "Subject", "Body")
    await sender.send_status_changed("customer@example.com", "so-123", "IN_PROGRESS")
    await sender.send_approval_request(message)
