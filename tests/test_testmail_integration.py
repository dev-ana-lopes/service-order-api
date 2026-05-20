from __future__ import annotations

from uuid import uuid4

import pytest

from src.infrastructure.email.smtp_client import SmtpEmailSender
from tests.support.testmail import (
    build_live_test_settings,
    build_testmail_recipient,
    is_testmail_live_enabled,
    message_recipients,
    message_text,
    wait_for_testmail_messages,
)


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.testmail
async def test_smtp_sender_delivers_message_to_testmail_live():
    settings = build_live_test_settings()
    if not is_testmail_live_enabled(settings):
        pytest.skip(
            "Testmail live test requires TESTMAIL_ENABLED=true, "
            "TESTMAIL_API_KEY and TESTMAIL_NAMESPACE"
        )

    sender = SmtpEmailSender(settings)
    tag = f"smtp-{uuid4().hex}"
    recipient = build_testmail_recipient(settings, tag)
    subject = f"SMTP Integration {tag}"
    body = f"Body for {tag}"

    await sender.send_email(recipient, subject, body)

    messages = wait_for_testmail_messages(settings, tag)

    assert messages, "No email received from Testmail API before timeout"
    assert any(subject in message_text(message) for message in messages)
    assert any(recipient in message_recipients(message) for message in messages)
    assert any(body in message_text(message) for message in messages)
