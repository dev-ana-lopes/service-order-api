from datetime import timedelta
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from src.domain.entities import ServiceOrder
from src.domain.enums import ServiceOrderStatus
from src.domain.time import utcnow
from src.infrastructure.config.settings import Settings, get_settings
from src.presentation.dependencies.db_dependencies import (
    get_catalog_service_repository,
    get_customer_repository,
    get_inventory_part_repository,
    get_service_order_repository,
    get_user_repository,
    get_vehicle_repository,
)
from tests.support import (
    MockCatalogServiceRepository,
    MockCustomerRepository,
    MockInventoryPartRepository,
    MockServiceOrderRepository,
    MockUserRepository,
    MockVehicleRepository,
    create_test_app,
)


def _build_settings(**overrides) -> Settings:
    base = {
        "DATABASE_URL": "postgresql+asyncpg://user:pass@localhost:5432/db",
        "JWT_SECRET": "super-secret",
        "SMTP_HOST": "mailhog",
        "SMTP_PORT": 1025,
        "SMTP_USE_TLS": False,
        "SMTP_USE_AUTH": False,
    }
    base.update(overrides)
    return Settings(**base)


@pytest_asyncio.fixture
async def admin_api_context():
    app = create_test_app()
    settings = _build_settings()
    user_repo = MockUserRepository()
    customer_repo = MockCustomerRepository()
    vehicle_repo = MockVehicleRepository()
    catalog_repo = MockCatalogServiceRepository()
    inventory_repo = MockInventoryPartRepository()
    service_order_repo = MockServiceOrderRepository()

    async def override_user_repo():
        return user_repo

    async def override_customer_repo():
        return customer_repo

    async def override_vehicle_repo():
        return vehicle_repo

    async def override_catalog_repo():
        return catalog_repo

    async def override_inventory_repo():
        return inventory_repo

    async def override_service_order_repo():
        return service_order_repo

    def override_settings():
        return settings

    app.dependency_overrides[get_settings] = override_settings
    app.dependency_overrides[get_user_repository] = override_user_repo
    app.dependency_overrides[get_customer_repository] = override_customer_repo
    app.dependency_overrides[get_vehicle_repository] = override_vehicle_repo
    app.dependency_overrides[get_catalog_service_repository] = override_catalog_repo
    app.dependency_overrides[get_inventory_part_repository] = override_inventory_repo
    app.dependency_overrides[get_service_order_repository] = override_service_order_repo

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield {
            "app": app,
            "client": client,
            "settings": settings,
            "service_order_repo": service_order_repo,
        }

    app.dependency_overrides.clear()


async def _authenticate(client: AsyncClient) -> str:
    register = await client.post(
        "/auth/register",
        json={"email": "admin@example.com", "password": "Admin1234"},
    )
    assert register.status_code == 201

    login = await client.post(
        "/auth/login",
        json={"email": "admin@example.com", "password": "Admin1234"},
    )
    assert login.status_code == 200
    return login.json()["access_token"]


@pytest.mark.asyncio
async def test_auth_register_login_and_protected_route(admin_api_context):
    client = admin_api_context["client"]

    unauthorized = await client.get("/customers")
    assert unauthorized.status_code == 401

    access_token = await _authenticate(client)
    response = await client.get(
        "/customers",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_customer_and_vehicle_crud(admin_api_context):
    client = admin_api_context["client"]
    access_token = await _authenticate(client)
    headers = {"Authorization": f"Bearer {access_token}"}

    customer_response = await client.post(
        "/customers",
        json={
            "name": "Maria",
            "cpf_cnpj": "111.444.777-35",
            "email": "maria@example.com",
            "phone": "11999999999",
        },
        headers=headers,
    )
    assert customer_response.status_code == 201
    customer_id = customer_response.json()["customer_id"]

    list_customers = await client.get("/customers", headers=headers)
    assert list_customers.status_code == 200
    assert list_customers.json()[0]["cpf_cnpj"] == "11144477735"

    vehicle_response = await client.post(
        "/vehicles",
        json={
            "customer_id": customer_id,
            "brand": "Fiat",
            "model": "Argo",
            "year": 2022,
            "plate": "BRA2A34",
        },
        headers=headers,
    )
    assert vehicle_response.status_code == 201
    vehicle_id = vehicle_response.json()["vehicle_id"]

    vehicle_detail = await client.get(f"/vehicles/{vehicle_id}", headers=headers)
    assert vehicle_detail.status_code == 200
    assert vehicle_detail.json()["plate"] == "BRA2A34"

    update_vehicle = await client.put(
        f"/vehicles/{vehicle_id}",
        json={
            "customer_id": customer_id,
            "brand": "Fiat",
            "model": "Pulse",
            "year": 2023,
            "plate": "ABC1234",
        },
        headers=headers,
    )
    assert update_vehicle.status_code == 200

    delete_vehicle = await client.delete(f"/vehicles/{vehicle_id}", headers=headers)
    assert delete_vehicle.status_code == 200
    assert delete_vehicle.json() == {"success": True}

    vehicle_after_delete = await client.get(f"/vehicles/{vehicle_id}", headers=headers)
    assert vehicle_after_delete.status_code == 404

    delete_customer = await client.delete(f"/customers/{customer_id}", headers=headers)
    assert delete_customer.status_code == 200
    assert delete_customer.json() == {"success": True}

    customer_after_delete = await client.get(
        f"/customers/{customer_id}", headers=headers
    )
    assert customer_after_delete.status_code == 404


@pytest.mark.asyncio
async def test_catalog_crud_and_metrics(admin_api_context):
    client = admin_api_context["client"]
    access_token = await _authenticate(client)
    headers = {"Authorization": f"Bearer {access_token}"}

    service_response = await client.post(
        "/catalog/services",
        json={"description": "Troca de oleo", "price": 150.0},
        headers=headers,
    )
    assert service_response.status_code == 201
    service_id = service_response.json()["service_id"]

    part_response = await client.post(
        "/catalog/parts",
        json={"name": "Filtro de ar", "unit_price": 80.0, "stock_quantity": 5},
        headers=headers,
    )
    assert part_response.status_code == 201
    part_id = part_response.json()["part_id"]

    get_service = await client.get(f"/catalog/services/{service_id}", headers=headers)
    get_part = await client.get(f"/catalog/parts/{part_id}", headers=headers)
    assert get_service.status_code == 200
    assert get_part.status_code == 200

    delete_service = await client.delete(
        f"/catalog/services/{service_id}",
        headers=headers,
    )
    assert delete_service.status_code == 200
    assert delete_service.json() == {"success": True}

    service_after_delete = await client.get(
        f"/catalog/services/{service_id}",
        headers=headers,
    )
    assert service_after_delete.status_code == 404

    delete_part = await client.delete(
        f"/catalog/parts/{part_id}",
        headers=headers,
    )
    assert delete_part.status_code == 200
    assert delete_part.json() == {"success": True}

    part_after_delete = await client.get(
        f"/catalog/parts/{part_id}",
        headers=headers,
    )
    assert part_after_delete.status_code == 404

    repo = admin_api_context["service_order_repo"]
    first = ServiceOrder(
        id=uuid4(),
        customer_id=uuid4(),
        vehicle_id=uuid4(),
        status=ServiceOrderStatus.FINISHED,
        created_at=utcnow() - timedelta(hours=2),
        updated_at=utcnow() - timedelta(hours=1),
        started_at=utcnow() - timedelta(hours=2),
        finished_at=utcnow() - timedelta(hours=1, minutes=30),
    )
    second = ServiceOrder(
        id=uuid4(),
        customer_id=uuid4(),
        vehicle_id=uuid4(),
        status=ServiceOrderStatus.FINISHED,
        created_at=utcnow() - timedelta(hours=5),
        updated_at=utcnow() - timedelta(hours=2),
        started_at=utcnow() - timedelta(hours=4),
        finished_at=utcnow() - timedelta(hours=3),
    )
    await repo.save(first)
    await repo.save(second)

    metrics_response = await client.get(
        "/metrics/average-execution-time", headers=headers
    )
    assert metrics_response.status_code == 200
    assert metrics_response.json()["average_execution_time_seconds"] == pytest.approx(
        2700.0
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "endpoint",
    [
        "/customers/00000000-0000-0000-0000-000000000001",
        "/vehicles/00000000-0000-0000-0000-000000000001",
        "/catalog/services/00000000-0000-0000-0000-000000000001",
        "/catalog/parts/00000000-0000-0000-0000-000000000001",
    ],
)
async def test_delete_admin_routes_require_authentication(admin_api_context, endpoint):
    response = await admin_api_context["client"].delete(endpoint)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_delete_admin_resources_return_404_when_missing(admin_api_context):
    client = admin_api_context["client"]
    access_token = await _authenticate(client)
    headers = {"Authorization": f"Bearer {access_token}"}

    missing_endpoints = [
        f"/customers/{uuid4()}",
        f"/vehicles/{uuid4()}",
        f"/catalog/services/{uuid4()}",
        f"/catalog/parts/{uuid4()}",
    ]

    for endpoint in missing_endpoints:
        response = await client.delete(endpoint, headers=headers)
        assert response.status_code == 404
