from __future__ import annotations

import os
from uuid import NAMESPACE_DNS, UUID, uuid4, uuid5

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from src.infrastructure.config.settings import Settings, get_settings
from src.infrastructure.email.approval_token_service import JwtApprovalTokenService
from src.presentation.dependencies import db_dependencies
from tests.support import create_test_app

pytestmark = [pytest.mark.asyncio, pytest.mark.integration]
INTEGRATION_TESTS_ENABLED = (
    os.getenv("INTEGRATION_TESTS_ENABLED", "false").lower() == "true"
)

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    (
        "postgresql+asyncpg://service_order_user:service_order_password@"
        "localhost:5432/service_order_db"
    ),
)


def _build_integration_settings() -> Settings:
    return Settings(
        DATABASE_URL=TEST_DATABASE_URL,
        APP_NAME="service-order-api-integration",
        APP_VERSION="2.1.0",
        ENVIRONMENT="test",
        APP_BASE_URL="http://testserver",
        EMAIL_PROVIDER="NOOP",
        SMTP_HOST="mailhog",
        SMTP_PORT=1025,
        SMTP_USE_TLS=False,
        SMTP_USE_AUTH=False,
        JWT_SECRET="integration-jwt-secret-with-32-characters",
        APPROVAL_TOKEN_SECRET="integration-approval-secret-with-32-chars",
        MIGRATE_ON_STARTUP=False,
    )


async def _truncate_tables() -> None:
    database = db_dependencies.database_session
    if database is None:
        return

    async with database.async_engine.begin() as connection:
        await connection.execute(
            text(
                "TRUNCATE TABLE "
                "part_items, "
                "service_items, "
                "service_orders, "
                "inventory_parts, "
                "catalog_services, "
                "vehicles, "
                "customers, "
                "users "
                "RESTART IDENTITY CASCADE"
            )
        )


async def _authenticate(client: AsyncClient) -> dict[str, str]:
    email = f"admin-{uuid4().hex[:8]}@example.com"
    password = "Admin1234"

    register = await client.post(
        "/auth/register",
        json={"email": email, "password": password},
    )
    assert register.status_code == 201

    login = await client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200

    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def _create_inline_service_order(
    client: AsyncClient,
    headers: dict[str, str],
    *,
    suffix: str,
) -> str:
    digest = uuid5(NAMESPACE_DNS, suffix).hex.upper()
    letters = "".join(ch for ch in digest if ch.isalpha())
    digits = "".join(ch for ch in digest if ch.isdigit())
    plate = f"{letters[:3]}{digits[0]}{letters[3]}{digits[1:3]}"

    response = await client.post(
        "/service-orders",
        headers=headers,
        json={
            "customer_name": f"Cliente {suffix}",
            "customer_email": f"cliente-{suffix}@example.com",
            "customer_phone": "11999999999",
            "vehicle_brand": "Toyota",
            "vehicle_model": "Corolla",
            "vehicle_year": 2023,
            "vehicle_plate": plate,
            "services": [{"description": "Revisao completa", "price": 220.0}],
            "parts": [{"name": "Filtro", "price": 35.0, "quantity": 1}],
        },
    )

    assert response.status_code == 201
    return response.json()["service_order_id"]


def _generate_token(
    settings: Settings,
    service_order_id: str,
    *,
    approved: bool,
) -> str:
    return JwtApprovalTokenService(settings).generate_token(
        UUID(service_order_id),
        approved=approved,
    )


@pytest_asyncio.fixture
async def integration_context():
    if not INTEGRATION_TESTS_ENABLED:
        pytest.skip(
            "Set INTEGRATION_TESTS_ENABLED=true to run PostgreSQL integration tests."
        )

    settings = _build_integration_settings()
    app = create_test_app()

    def override_settings() -> Settings:
        return settings

    app.dependency_overrides[get_settings] = override_settings
    db_dependencies.database_session = None
    db_dependencies.init_database(settings)
    if db_dependencies.database_session is None:
        pytest.skip("Database session could not be initialized for integration tests.")
    if not await db_dependencies.database_session.ping():
        await db_dependencies.database_session.dispose()
        db_dependencies.database_session = None
        pytest.skip(f"Integration database is not reachable at {TEST_DATABASE_URL}.")
    await _truncate_tables()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield {
            "client": client,
            "headers": await _authenticate(client),
            "settings": settings,
        }

    await _truncate_tables()
    if db_dependencies.database_session is not None:
        await db_dependencies.database_session.dispose()
    db_dependencies.database_session = None
    app.dependency_overrides.clear()


async def test_open_service_order_and_query_status_with_real_postgres(
    integration_context,
):
    client = integration_context["client"]
    headers = integration_context["headers"]

    service_order_id = await _create_inline_service_order(
        client,
        headers,
        suffix="open01",
    )

    detail = await client.get(f"/service-orders/{service_order_id}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["budget_total"] == 255.0
    assert detail.json()["status"] == "WAITING_APPROVAL"

    status_response = await client.get(
        f"/service-orders/{service_order_id}/status",
        headers=headers,
    )
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "WAITING_APPROVAL"


async def test_public_approval_and_external_notification_flow_with_real_postgres(
    integration_context,
):
    client = integration_context["client"]
    headers = integration_context["headers"]
    settings = integration_context["settings"]

    approved_order_id = await _create_inline_service_order(
        client,
        headers,
        suffix="pubok1",
    )
    approve_token = _generate_token(settings, approved_order_id, approved=True)

    public_get = await client.get(
        f"/public/service-orders/{approved_order_id}/approval",
        params={"token": approve_token},
    )
    assert public_get.status_code == 200
    assert public_get.json()["decision"] == "APPROVED"
    assert public_get.json()["status"] == "IN_PROGRESS"
    approved_public_status = await client.get(
        f"/public/service-orders/{approved_order_id}/status",
    )
    assert approved_public_status.status_code == 200
    assert approved_public_status.json()["status"] == "IN_PROGRESS"
    assert approved_public_status.json()["approval_decision"] == "APPROVED"

    rejected_order_id = await _create_inline_service_order(
        client,
        headers,
        suffix="pubno1",
    )
    reject_token = _generate_token(settings, rejected_order_id, approved=False)

    public_post = await client.post(
        f"/public/service-orders/{rejected_order_id}/approval",
        json={"token": reject_token},
    )
    assert public_post.status_code == 200
    assert public_post.json()["decision"] == "REJECTED"
    assert public_post.json()["status"] == "DIAGNOSIS"

    public_status = await client.get(
        f"/public/service-orders/{rejected_order_id}/status",
    )
    assert public_status.status_code == 200
    assert public_status.json()["status"] == "DIAGNOSIS"
    assert public_status.json()["approval_decision"] == "REJECTED"

    rejected_detail = await client.get(
        f"/service-orders/{rejected_order_id}",
        headers=headers,
    )
    assert rejected_detail.status_code == 200
    assert rejected_detail.json()["status"] == "DIAGNOSIS"
    assert rejected_detail.json()["approval_decision"] == "REJECTED"


async def test_active_list_orders_by_priority_and_hides_finished_and_delivered_in_db(
    integration_context,
):
    client = integration_context["client"]
    headers = integration_context["headers"]
    settings = integration_context["settings"]

    waiting_order_id = await _create_inline_service_order(
        client,
        headers,
        suffix="wait01",
    )

    diagnosis_order_id = await _create_inline_service_order(
        client,
        headers,
        suffix="diag01",
    )
    reject_token = _generate_token(settings, diagnosis_order_id, approved=False)
    reject_response = await client.post(
        f"/public/service-orders/{diagnosis_order_id}/approval",
        json={"token": reject_token},
    )
    assert reject_response.status_code == 200

    in_progress_order_id = await _create_inline_service_order(
        client,
        headers,
        suffix="prog01",
    )
    approve_token = _generate_token(settings, in_progress_order_id, approved=True)
    approve_response = await client.get(
        f"/public/service-orders/{in_progress_order_id}/approval",
        params={"token": approve_token},
    )
    assert approve_response.status_code == 200

    delivered_order_id = await _create_inline_service_order(
        client,
        headers,
        suffix="done01",
    )
    delivered_token = _generate_token(settings, delivered_order_id, approved=True)
    delivered_approval = await client.get(
        f"/public/service-orders/{delivered_order_id}/approval",
        params={"token": delivered_token},
    )
    assert delivered_approval.status_code == 200
    finished_update = await client.patch(
        f"/service-orders/{delivered_order_id}/status",
        headers=headers,
        json={"status": "FINISHED"},
    )
    assert finished_update.status_code == 200
    delivered_update = await client.patch(
        f"/service-orders/{delivered_order_id}/status",
        headers=headers,
        json={"status": "DELIVERED"},
    )
    assert delivered_update.status_code == 200

    response = await client.get("/service-orders/active", headers=headers)

    assert response.status_code == 200
    assert [item["status"] for item in response.json()] == [
        "IN_PROGRESS",
        "WAITING_APPROVAL",
        "DIAGNOSIS",
    ]
    assert [item["id"] for item in response.json()] == [
        in_progress_order_id,
        waiting_order_id,
        diagnosis_order_id,
    ]
