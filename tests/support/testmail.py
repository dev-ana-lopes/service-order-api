from __future__ import annotations

import os
import re
import time
from typing import Iterable

import httpx

from src.infrastructure.config.settings import Settings


def build_live_test_settings() -> Settings:
    return Settings(
        DATABASE_URL=os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://user:pass@localhost:5432/service_order_db",
        ),
        JWT_SECRET=os.getenv(
            "JWT_SECRET",
            "test-jwt-secret-with-at-least-32-characters",
        ),
        APPROVAL_TOKEN_SECRET=os.getenv(
            "APPROVAL_TOKEN_SECRET",
            "test-approval-secret-with-at-least-32-chars",
        ),
        APP_BASE_URL=os.getenv("APP_BASE_URL", "http://localhost:8000"),
        SMTP_HOST=os.getenv("SMTP_HOST", "mailhog"),
        SMTP_PORT=int(os.getenv("SMTP_PORT", "1025")),
        SMTP_FROM_EMAIL=os.getenv("SMTP_FROM_EMAIL", "no-reply@localhost"),
        SMTP_USERNAME=os.getenv("SMTP_USERNAME", ""),
        SMTP_PASSWORD=os.getenv("SMTP_PASSWORD", ""),
        SMTP_USE_TLS=os.getenv("SMTP_USE_TLS", "false").lower() == "true",
        SMTP_USE_AUTH=os.getenv("SMTP_USE_AUTH", "false").lower() == "true",
        SMTP_TIMEOUT_SECONDS=int(os.getenv("SMTP_TIMEOUT_SECONDS", "10")),
        TESTMAIL_API_KEY=os.getenv("TESTMAIL_API_KEY", ""),
        TESTMAIL_NAMESPACE=os.getenv("TESTMAIL_NAMESPACE", ""),
        TESTMAIL_ENABLED=os.getenv("TESTMAIL_ENABLED", "false").lower() == "true",
        TESTMAIL_API_BASE_URL=os.getenv(
            "TESTMAIL_API_BASE_URL",
            "https://api.testmail.app/api/json",
        ),
    )


def is_testmail_live_enabled(settings: Settings) -> bool:
    return bool(
        settings.TESTMAIL_ENABLED
        and settings.TESTMAIL_API_KEY
        and settings.TESTMAIL_NAMESPACE
        and not (settings.SMTP_HOST == "mailhog" and settings.SMTP_PORT == 1025)
    )


def build_testmail_recipient(settings: Settings, tag: str) -> str:
    return f"{settings.TESTMAIL_NAMESPACE}.{tag}@inbox.testmail.app"


def extract_email_list(payload: object) -> list[dict]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("emails", "messages", "result"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []


def message_text(message: dict) -> str:
    text_parts = []
    for key in ("text", "html", "body", "subject"):
        value = message.get(key)
        if isinstance(value, str):
            text_parts.append(value)
    return "\n".join(text_parts)


def message_recipients(message: dict) -> str:
    recipient_fields = []
    for key in ("to", "deliveredTo", "destination"):
        value = message.get(key)
        if isinstance(value, str):
            recipient_fields.append(value)
        elif isinstance(value, list):
            recipient_fields.extend(str(item) for item in value)
    return " ".join(recipient_fields)


def fetch_testmail_messages(settings: Settings, tag: str) -> list[dict]:
    params = {
        "apikey": settings.TESTMAIL_API_KEY,
        "namespace": settings.TESTMAIL_NAMESPACE,
        "tag": tag,
    }
    response = httpx.get(settings.TESTMAIL_API_BASE_URL, params=params, timeout=10.0)
    response.raise_for_status()
    return extract_email_list(response.json())


def wait_for_testmail_messages(
    settings: Settings,
    tag: str,
    *,
    timeout_seconds: int = 30,
    poll_interval_seconds: int = 2,
) -> list[dict]:
    deadline = time.monotonic() + timeout_seconds
    messages = []
    while time.monotonic() < deadline:
        messages = fetch_testmail_messages(settings, tag)
        if messages:
            return messages
        time.sleep(poll_interval_seconds)
    return messages


def extract_links(text: str) -> list[str]:
    return re.findall(r"https?://[^\s]+", text)


def first_matching_link(links: Iterable[str], pattern: str) -> str | None:
    for link in links:
        if pattern in link:
            return link
    return None
