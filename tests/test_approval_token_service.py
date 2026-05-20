from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from src.domain.errors import ExpiredApprovalTokenError, InvalidApprovalTokenError
from src.infrastructure.config.settings import Settings
from src.infrastructure.email.approval_token_service import JwtApprovalTokenService


def _build_settings(**overrides) -> Settings:
    base = {
        "DATABASE_URL": "postgresql+asyncpg://user:pass@localhost:5432/db",
        "SMTP_HOST": "mailhog",
        "SMTP_PORT": 1025,
        "JWT_SECRET": "jwt-secret",
        "APPROVAL_TOKEN_SECRET": "approval-secret",
        "APPROVAL_TOKEN_TTL_MINUTES": 15,
    }
    base.update(overrides)
    return Settings(**base)


def test_generate_and_verify_approval_token():
    service = JwtApprovalTokenService(_build_settings())
    service_order_id = uuid4()

    token = service.generate_token(service_order_id, approved=True)
    payload = service.verify_token(token)

    assert payload.service_order_id == service_order_id
    assert payload.approved is True
    assert payload.expires_at > datetime.now(timezone.utc)


def test_verify_approval_token_rejects_invalid_signature():
    service = JwtApprovalTokenService(_build_settings())

    with pytest.raises(InvalidApprovalTokenError):
        service.verify_token("invalid.token.value")


def test_verify_approval_token_rejects_expired_token():
    settings = _build_settings(APPROVAL_TOKEN_TTL_MINUTES=-1)
    service = JwtApprovalTokenService(settings)
    token = service.generate_token(uuid4(), approved=False)

    with pytest.raises(ExpiredApprovalTokenError):
        service.verify_token(token)


def test_verify_approval_token_rejects_wrong_purpose():
    settings = _build_settings()
    service = JwtApprovalTokenService(settings)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
    from jose import jwt

    token = jwt.encode(
        {
            "sub": str(uuid4()),
            "decision": "approve",
            "purpose": "not-service-order-approval",
            "exp": expires_at,
        },
        settings.approval_token_secret,
        algorithm=settings.JWT_ALGORITHM,
    )

    with pytest.raises(InvalidApprovalTokenError):
        service.verify_token(token)
