from __future__ import annotations

import base64
import os
import re
import time
from urllib.parse import parse_qs, urlparse
from uuid import NAMESPACE_DNS, uuid4, uuid5

import httpx
import pytest

API_BASE_URL = os.getenv("MAILHOG_E2E_API_URL", "http://localhost:8000").rstrip("/")
MAILHOG_API_URL = os.getenv("MAILHOG_API_URL", "http://localhost:8025").rstrip("/")
MAILHOG_E2E_ENABLED = os.getenv("MAILHOG_E2E_ENABLED", "false").lower() == "true"


def _generate_plate(seed: str) -> str:
    digest = uuid5(NAMESPACE_DNS, seed).hex.upper()
    letters = "".join(char for char in digest if char.isalpha())
    digits = "".join(char for char in digest if char.isdigit())
    return f"{letters[:3]}{digits[0]}{letters[3]}{digits[1:3]}"


def _decode_mailhog_body(message: dict) -> str:
    parts = (message.get("MIME") or {}).get("Parts") or []
    if not parts:
        return str((message.get("Content") or {}).get("Body", ""))

    part = parts[0]
    headers = part.get("Headers") or {}
    encoding = "".join(headers.get("Content-Transfer-Encoding", [])).lower()
    body = str(part.get("Body", ""))
    if encoding == "base64":
        return base64.b64decode(body).decode("utf-8")
    return body


def _message_recipients(message: dict) -> str:
    recipients = []
    for recipient in message.get("To", []):
        mailbox = recipient.get("Mailbox")
        domain = recipient.get("Domain")
        if mailbox and domain:
            recipients.append(f"{mailbox}@{domain}")
    return " ".join(recipients)


def _wait_for_rejection_email(
    client: httpx.Client,
    *,
    recipient: str,
    service_order_id: str,
    timeout_seconds: int = 45,
) -> str:
    deadline = time.monotonic() + timeout_seconds
    recipient_lower = recipient.lower()

    while time.monotonic() < deadline:
        response = client.get(f"{MAILHOG_API_URL}/api/v2/messages")
        response.raise_for_status()
        items = response.json().get("items", [])

        for item in reversed(items):
            body = _decode_mailhog_body(item)
            recipients = _message_recipients(item).lower()
            if (
                recipient_lower in recipients
                and service_order_id in body
                and "Rejeitar:" in body
            ):
                return body

        time.sleep(2)

    raise AssertionError("Approval email with rejection link was not found in MailHog")


def _extract_reject_link(body: str) -> str:
    match = re.search(r"Rejeitar:\s*(https?://[^\s]+)", body)
    assert match, f"Reject link not found in email body: {body}"
    return match.group(1)


@pytest.mark.e2e
@pytest.mark.mailhog
def test_mailhog_rejection_flow_updates_budget_decision_and_status():
    if not MAILHOG_E2E_ENABLED:
        pytest.skip(
            "Set MAILHOG_E2E_ENABLED=true to run the local MailHog rejection flow."
        )

    with httpx.Client(base_url=API_BASE_URL, timeout=15.0) as client:
        try:
            health = client.get("/health/ready")
            health.raise_for_status()
            mailhog = client.get(f"{MAILHOG_API_URL}/api/v2/messages")
            mailhog.raise_for_status()
        except httpx.HTTPError as exc:
            pytest.skip(f"Local stack is not available for MailHog E2E: {exc}")

        unique = uuid4().hex[:8]
        admin_email = f"mailhog-admin-{unique}@example.com"
        recipient_email = f"mailhog-customer-{unique}@example.com"
        password = "Admin1234"

        register = client.post(
            "/auth/register",
            json={"email": admin_email, "password": password},
        )
        assert register.status_code == 201

        login = client.post(
            "/auth/login",
            json={"email": admin_email, "password": password},
        )
        assert login.status_code == 200
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        create_order = client.post(
            "/service-orders",
            headers=headers,
            json={
                "customer_name": f"Cliente MailHog {unique}",
                "customer_email": recipient_email,
                "customer_phone": "11999999999",
                "vehicle_brand": "Toyota",
                "vehicle_model": "Corolla",
                "vehicle_year": 2024,
                "vehicle_plate": _generate_plate(unique),
                "services": [{"description": "Revisao completa", "price": 220.0}],
                "parts": [{"name": "Filtro", "price": 35.0, "quantity": 1}],
            },
        )
        assert create_order.status_code == 201
        service_order_id = create_order.json()["service_order_id"]

        email_body = _wait_for_rejection_email(
            client,
            recipient=recipient_email,
            service_order_id=service_order_id,
        )
        reject_link = _extract_reject_link(email_body)
        parsed_url = urlparse(reject_link)
        reject_token = parse_qs(parsed_url.query)["token"][0]

        rejection_response = client.get(
            parsed_url.path,
            params={"token": reject_token},
        )
        assert rejection_response.status_code == 200
        assert rejection_response.json()["decision"] == "REJECTED"
        assert rejection_response.json()["status"] == "DIAGNOSIS"

        public_status = client.get(f"/public/service-orders/{service_order_id}/status")
        assert public_status.status_code == 200
        assert public_status.json() == {
            "status": "DIAGNOSIS",
            "approval_decision": "REJECTED",
            "rejection_reason": None,
        }

        detail = client.get(f"/service-orders/{service_order_id}", headers=headers)
        assert detail.status_code == 200
        assert detail.json()["status"] == "DIAGNOSIS"
        assert detail.json()["approval_decision"] == "REJECTED"

        status = client.get(
            f"/service-orders/{service_order_id}/status", headers=headers
        )
        assert status.status_code == 200
        assert status.json() == {
            "status": "DIAGNOSIS",
            "approval_decision": "REJECTED",
            "rejection_reason": None,
        }
