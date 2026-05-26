from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, PrivateAttr, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


def _parse_csv_or_json_list(value: str | list[str]) -> list[str]:
    if isinstance(value, list):
        return value

    raw_value = value.strip()
    if not raw_value:
        return []

    if raw_value.startswith("["):
        parsed = json.loads(raw_value)
        if not isinstance(parsed, list):
            raise ValueError("Expected a JSON array for list-based settings")
        return [str(item).strip() for item in parsed if str(item).strip()]

    return [item.strip() for item in raw_value.split(",") if item.strip()]


def _resolve_secret(raw_value: str, file_path: str | None, field_name: str) -> str:
    if raw_value.strip():
        return raw_value.strip()

    if not file_path:
        return ""

    content = Path(file_path).read_text(encoding="utf-8").strip()
    if not content:
        raise ValueError(f"{field_name}_FILE is empty")
    return content


def _looks_like_placeholder(value: str) -> bool:
    lowered = value.lower()
    return any(
        marker in lowered
        for marker in (
            "change-me",
            "your-secret",
            "example.com",
            "localhost",
            "ec2_public_dns_or_ip",
        )
    )


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    _otel_fastapi_instrumentor: object | None = PrivateAttr(default=None)
    _otel_sqlalchemy_instrumentor: object | None = PrivateAttr(default=None)

    APP_NAME: str = "service-order-api"
    APP_VERSION: str = "3.0.0"
    ENVIRONMENT: Literal["development", "test", "staging", "production"] = "development"
    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = False
    EMAIL_PROVIDER: Literal["SMTP", "NOOP"] = "SMTP"
    CORS_ALLOWED_ORIGINS: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: [
            "http://localhost",
            "http://localhost:3000",
            "http://localhost:5173",
            "http://localhost:8000",
        ]
    )
    CORS_ALLOW_CREDENTIALS: bool = True
    TRUSTED_HOSTS: Annotated[list[str], NoDecode] = Field(default_factory=lambda: ["*"])
    DATABASE_URL: str
    APP_BASE_URL: str = "http://localhost:8000"
    SMTP_HOST: str = "mailhog"
    SMTP_PORT: int = 1025
    SMTP_FROM_EMAIL: str = ""
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_PASSWORD_FILE: str | None = None
    SMTP_USE_TLS: bool = True
    SMTP_USE_AUTH: bool = True
    SMTP_TIMEOUT_SECONDS: int = 10
    TESTMAIL_API_KEY: str = ""
    TESTMAIL_NAMESPACE: str = ""
    TESTMAIL_ENABLED: bool = False
    TESTMAIL_API_BASE_URL: str = "https://api.testmail.app/api/json"
    APPROVAL_TOKEN_SECRET: str = ""
    APPROVAL_TOKEN_SECRET_FILE: str | None = None
    APPROVAL_TOKEN_TTL_MINUTES: int = 60
    JWT_SECRET: str
    JWT_SECRET_FILE: str | None = None
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60
    CUSTOMER_JWT_SECRET: str = ""
    CUSTOMER_JWT_SECRET_FILE: str | None = None
    CUSTOMER_JWT_ALGORITHM: str = "HS256"
    CUSTOMER_JWT_ISSUER: str = "service-order-auth-lambda/development"
    HEALTHCHECK_TIMEOUT_SECONDS: int = 5
    MIGRATE_ON_STARTUP: bool = True
    DD_SERVICE: str = "service-order-api"
    DD_ENV: str = "development"
    DD_VERSION: str = "3.0.0"
    DD_API_KEY: str = ""
    DD_TRACE_ENABLED: bool = False
    OTEL_ENABLED: bool = False
    OTEL_SERVICE_NAME: str = "service-order-api"
    OTEL_EXPORTER_OTLP_ENDPOINT: str = ""

    @field_validator("CORS_ALLOWED_ORIGINS", "TRUSTED_HOSTS", mode="before")
    @classmethod
    def parse_list_settings(cls, value: str | list[str]) -> list[str]:
        return _parse_csv_or_json_list(value)

    @field_validator("LOG_LEVEL")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        return value.upper()

    @field_validator("EMAIL_PROVIDER", mode="before")
    @classmethod
    def normalize_email_provider(cls, value: str) -> str:
        return value.upper()

    @model_validator(mode="after")
    def validate_configuration(self) -> "Settings":
        self.JWT_SECRET = _resolve_secret(
            self.JWT_SECRET,
            self.JWT_SECRET_FILE,
            "JWT_SECRET",
        )
        self.CUSTOMER_JWT_SECRET = _resolve_secret(
            self.CUSTOMER_JWT_SECRET,
            self.CUSTOMER_JWT_SECRET_FILE,
            "CUSTOMER_JWT_SECRET",
        )
        self.APPROVAL_TOKEN_SECRET = _resolve_secret(
            self.APPROVAL_TOKEN_SECRET,
            self.APPROVAL_TOKEN_SECRET_FILE,
            "APPROVAL_TOKEN_SECRET",
        )
        self.SMTP_PASSWORD = _resolve_secret(
            self.SMTP_PASSWORD,
            self.SMTP_PASSWORD_FILE,
            "SMTP_PASSWORD",
        )
        self.DD_ENV = self.ENVIRONMENT
        self.DD_VERSION = self.APP_VERSION

        if self.ENVIRONMENT in {"staging", "production"}:
            if len(self.JWT_SECRET) < 32 or _looks_like_placeholder(self.JWT_SECRET):
                raise ValueError(
                    "JWT_SECRET must be a strong non-placeholder secret "
                    "in staging/production"
                )

            if self.CUSTOMER_JWT_SECRET and len(self.CUSTOMER_JWT_SECRET) < 32:
                raise ValueError(
                    "CUSTOMER_JWT_SECRET must be strong in staging/production"
                )

            if len(self.approval_token_secret) < 32 or _looks_like_placeholder(
                self.approval_token_secret
            ):
                raise ValueError(
                    "APPROVAL_TOKEN_SECRET must be a strong non-placeholder secret "
                    "in staging/production"
                )

            if self.approval_token_secret == self.JWT_SECRET:
                raise ValueError(
                    "APPROVAL_TOKEN_SECRET must be different from JWT_SECRET "
                    "in staging/production"
                )

            if self.CUSTOMER_JWT_SECRET and self.CUSTOMER_JWT_SECRET == self.JWT_SECRET:
                raise ValueError(
                    "CUSTOMER_JWT_SECRET must be different from JWT_SECRET "
                    "in staging/production"
                )

            if _looks_like_placeholder(self.APP_BASE_URL):
                raise ValueError(
                    "APP_BASE_URL must point to the real public API address "
                    "in staging/production"
                )

            if "*" in self.CORS_ALLOWED_ORIGINS:
                raise ValueError(
                    "CORS_ALLOWED_ORIGINS cannot use '*' in staging/production"
                )

        return self

    @property
    def database_url_async(self) -> str:
        return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

    @property
    def approval_token_secret(self) -> str:
        return self.APPROVAL_TOKEN_SECRET or self.JWT_SECRET


def get_settings() -> Settings:
    env_file = os.environ.get("APP_ENV_FILE") or ".env"
    return Settings(_env_file=env_file)
