from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from src.infrastructure.config.settings import Settings, get_settings
from src.presentation.dependencies.db_dependencies import get_database_session
from tests.support import create_test_app


def _build_settings(**overrides) -> Settings:
    base = {
        "DATABASE_URL": "postgresql+asyncpg://user:pass@localhost:5432/db",
        "JWT_SECRET": "super-secret-value-with-32-characters",
        "APPROVAL_TOKEN_SECRET": "approval-secret-value-with-32-chars",
        "SMTP_HOST": "mailhog",
        "SMTP_PORT": 1025,
        "SMTP_USE_TLS": False,
        "SMTP_USE_AUTH": False,
        "APP_BASE_URL": "http://testserver",
    }
    base.update(overrides)
    return Settings(**base)


class _HealthyDatabaseSession:
    async def ping(self) -> bool:
        return True


class _UnhealthyDatabaseSession:
    async def ping(self) -> bool:
        return False


def test_settings_support_secret_files(tmp_path: Path):
    jwt_secret_file = tmp_path / "jwt.secret"
    approval_secret_file = tmp_path / "approval.secret"
    smtp_password_file = tmp_path / "smtp.secret"
    jwt_secret_file.write_text("jwt-secret-from-file-1234567890", encoding="utf-8")
    approval_secret_file.write_text(
        "approval-secret-from-file-1234567890",
        encoding="utf-8",
    )
    smtp_password_file.write_text("smtp-password-from-file", encoding="utf-8")

    settings = Settings(
        DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/db",
        JWT_SECRET="",
        JWT_SECRET_FILE=str(jwt_secret_file),
        APPROVAL_TOKEN_SECRET="",
        APPROVAL_TOKEN_SECRET_FILE=str(approval_secret_file),
        SMTP_PASSWORD="",
        SMTP_PASSWORD_FILE=str(smtp_password_file),
        SMTP_USE_AUTH=False,
    )

    assert settings.JWT_SECRET == "jwt-secret-from-file-1234567890"
    assert settings.approval_token_secret == "approval-secret-from-file-1234567890"
    assert settings.SMTP_PASSWORD == "smtp-password-from-file"


def test_settings_reject_unsafe_production_defaults():
    with pytest.raises(ValidationError):
        Settings(
            DATABASE_URL=(
                "postgresql+asyncpg://service_order_user:password@db.internal:5432/"
                "service_order_db"
            ),
            ENVIRONMENT="production",
            APP_BASE_URL="http://localhost:8000",
            SMTP_HOST="localhost",
            SMTP_USE_AUTH=False,
            SMTP_FROM_EMAIL="",
            JWT_SECRET="change-me",
            APPROVAL_TOKEN_SECRET="change-me-too",
        )


def test_settings_allow_noop_email_provider_in_production_demo_mode():
    settings = Settings(
        DATABASE_URL=(
            "postgresql+asyncpg://service_order_user:password@db.internal:5432/"
            "service_order_db"
        ),
        ENVIRONMENT="production",
        EMAIL_PROVIDER="noop",
        APP_BASE_URL="https://api.workshop-demo.fiap",
        SMTP_HOST="mailhog",
        SMTP_USE_AUTH=False,
        SMTP_FROM_EMAIL="",
        JWT_SECRET="jwt-secret-value-with-32-characters",
        APPROVAL_TOKEN_SECRET="approval-secret-value-with-32-chars",
        CORS_ALLOWED_ORIGINS=["https://app.workshop-demo.fiap"],
        TRUSTED_HOSTS=["api.workshop-demo.fiap"],
    )

    assert settings.EMAIL_PROVIDER == "NOOP"


def test_settings_allow_optional_smtp_values_in_production():
    settings = Settings(
        DATABASE_URL=(
            "postgresql+asyncpg://service_order_user:password@db.internal:5432/"
            "service_order_db"
        ),
        ENVIRONMENT="production",
        EMAIL_PROVIDER="SMTP",
        APP_BASE_URL="https://api.workshop-demo.fiap",
        SMTP_HOST="",
        SMTP_FROM_EMAIL="",
        SMTP_USERNAME="",
        SMTP_PASSWORD="",
        CORS_ALLOWED_ORIGINS=["https://app.workshop-demo.fiap"],
        TRUSTED_HOSTS=["api.workshop-demo.fiap"],
        JWT_SECRET="jwt-secret-value-with-32-characters",
        APPROVAL_TOKEN_SECRET="approval-secret-value-with-32-chars",
    )

    assert settings.EMAIL_PROVIDER == "SMTP"
    assert settings.SMTP_HOST == ""


@pytest_asyncio.fixture
async def health_app():
    app = create_test_app()
    settings = _build_settings(APP_NAME="service-order-api-test", APP_VERSION="9.9.9")

    def override_settings():
        return settings

    def override_database_session():
        return _HealthyDatabaseSession()

    app.dependency_overrides[get_settings] = override_settings
    app.dependency_overrides[get_database_session] = override_database_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield {"app": app, "client": client}

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_health_and_readiness_endpoints_return_operational_status(health_app):
    health_response = await health_app["client"].get("/health")
    readiness_response = await health_app["client"].get("/health/ready")

    assert health_response.status_code == 200
    assert health_response.json() == {
        "status": "ok",
        "service": "service-order-api-test",
        "version": "9.9.9",
        "environment": "development",
    }
    assert readiness_response.status_code == 200
    assert readiness_response.json()["checks"]["database"] == "ok"


@pytest.mark.asyncio
async def test_readiness_endpoint_returns_503_when_database_is_unavailable():
    app = create_test_app()
    settings = _build_settings()

    def override_settings():
        return settings

    def override_database_session():
        return _UnhealthyDatabaseSession()

    app.dependency_overrides[get_settings] = override_settings
    app.dependency_overrides[get_database_session] = override_database_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/health/ready")

    app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json()["detail"] == "Database is unavailable"
