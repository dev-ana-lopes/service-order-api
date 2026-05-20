import pytest

from src.infrastructure.database.url_utils import (
    describe_database_target,
    normalize_postgresql_url_for_alembic,
    validate_runtime_database_url,
)


def test_normalize_postgresql_url_for_alembic_supports_runtime_and_legacy_schemes():
    assert (
        normalize_postgresql_url_for_alembic(
            "postgresql+asyncpg://user:pass@db:5432/service_order_db"
        )
        == "postgresql+psycopg://user:pass@db:5432/service_order_db"
    )
    assert (
        normalize_postgresql_url_for_alembic(
            "postgresql://user:pass@db:5432/service_order_db"
        )
        == "postgresql+psycopg://user:pass@db:5432/service_order_db"
    )
    assert (
        normalize_postgresql_url_for_alembic(
            "postgres://user:pass@db:5432/service_order_db"
        )
        == "postgresql+psycopg://user:pass@db:5432/service_order_db"
    )


def test_normalize_postgresql_url_for_alembic_keeps_explicit_sync_driver():
    url = "postgresql+psycopg://user:pass@db:5432/service_order_db"
    assert normalize_postgresql_url_for_alembic(url) == url


def test_describe_database_target_extracts_host_port_and_database():
    assert describe_database_target(
        "postgresql+asyncpg://user:pass@db.example:5433/service_order_db"
    ) == ("db.example", 5433, "service_order_db")


def test_validate_runtime_database_url_accepts_real_hosts():
    database_url = (
        "postgresql+asyncpg://user:pass@service-order-db.abc123.sa-east-1."
        "rds.amazonaws.com:5432/service_order_db"
    )
    assert validate_runtime_database_url(database_url) == (
        "service-order-db.abc123.sa-east-1.rds.amazonaws.com",
        5432,
        "service_order_db",
    )


@pytest.mark.parametrize(
    "database_url,error_message",
    [
        ("", "DATABASE_URL environment variable is required."),
        (
            "postgresql+asyncpg://user:pass@SEU_HOST_POSTGRES:5432/service_order_db",
            "DATABASE_URL host still uses a placeholder value.",
        ),
        (
            "postgresql+asyncpg://user:pass@:5432/service_order_db",
            "DATABASE_URL must include a database host.",
        ),
    ],
)
def test_validate_runtime_database_url_rejects_invalid_runtime_values(
    database_url, error_message
):
    with pytest.raises(ValueError, match=error_message):
        validate_runtime_database_url(database_url)
