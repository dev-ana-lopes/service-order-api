from urllib.parse import urlsplit

PLACEHOLDER_DATABASE_HOSTS = {
    "seu_host_postgres",
    "your-rds-endpoint",
    "endpoint-rds",
    "db-host",
}


def normalize_postgresql_url_for_alembic(database_url: str) -> str:
    if database_url.startswith("postgresql+asyncpg://"):
        return database_url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+psycopg://", 1)
    return database_url


def describe_database_target(database_url: str) -> tuple[str, int, str]:
    parsed = urlsplit(database_url)
    host = parsed.hostname or ""
    port = parsed.port or 5432
    database = parsed.path.lstrip("/") or "<unknown>"
    return host, port, database


def validate_runtime_database_url(database_url: str) -> tuple[str, int, str]:
    if not database_url.strip():
        raise ValueError("DATABASE_URL environment variable is required.")

    host, port, database = describe_database_target(database_url)
    normalized_host = host.strip().lower()

    if not host:
        raise ValueError("DATABASE_URL must include a database host.")

    if normalized_host in PLACEHOLDER_DATABASE_HOSTS:
        raise ValueError(
            "DATABASE_URL host still uses a placeholder value. "
            "Replace it with the real RDS endpoint."
        )

    return host, port, database
