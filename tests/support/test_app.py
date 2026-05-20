from fastapi import FastAPI

from src.infrastructure.config.settings import Settings
from src.main import create_app



def create_test_app() -> FastAPI:
    settings = Settings(
        DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/db",
        JWT_SECRET="super-secret-value-with-32-characters",
        CUSTOMER_JWT_SECRET="customer-secret-value-with-32-chars",
        APPROVAL_TOKEN_SECRET="approval-secret-value-with-32-chars",
        SMTP_HOST="mailhog",
        SMTP_PORT=1025,
        SMTP_USE_TLS=False,
        SMTP_USE_AUTH=False,
        APP_BASE_URL="http://testserver",
        ENVIRONMENT="test",
        LOG_JSON=True,
        OTEL_ENABLED=False,
    )
    return create_app(settings)
