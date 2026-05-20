from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from jose import jwt

from src.domain.contracts.token_verifier import AuthenticatedPrincipal
from src.domain.entities import CatalogService, Customer, ServiceOrder, Vehicle
from src.domain.enums import ServiceOrderStatus
from src.domain.time import utcnow
from src.infrastructure.config.settings import Settings, get_settings
from src.presentation.dependencies.auth import require_customer_or_admin_principal
from src.presentation.dependencies.db_dependencies import (
    get_catalog_service_repository,
    get_customer_repository,
    get_email_sender,
    get_inventory_part_repository,
    get_part_item_repository,
    get_service_item_repository,
    get_service_order_repository,
    get_vehicle_repository,
)
from tests.support import (
    MockApprovalTokenService,
    MockCatalogServiceRepository,
    MockCustomerRepository,
    MockEmailSender,
    MockInventoryPartRepository,
    MockPartItemRepository,
    MockServiceItemRepository,
    MockServiceOrderRepository,
    MockVehicleRepository,
    create_test_app,
)


TEST_CUSTOMER_ID = UUID("11111111-1111-1111-1111-111111111111")


@pytest_asyncio.fixture
async def phase3_customer_context():
    app = create_test_app()
    settings = Settings(
        DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/db",
        JWT_SECRET="admin-secret-value-with-32-characters",
        CUSTOMER_JWT_SECRET="customer-secret-value-with-32-characters",
        CUSTOMER_JWT_ISSUER="service-order-auth-lambda/test",
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
    customer_repo = MockCustomerRepository()
    vehicle_repo = MockVehicleRepository()
    service_order_repo = MockServiceOrderRepository()
    service_item_repo = MockServiceItemRepository()
    part_item_repo = MockPartItemRepository()
    catalog_repo = MockCatalogServiceRepository()
    inventory_repo = MockInventoryPartRepository()
    email_sender = MockEmailSender()
    approval_token_service = MockApprovalTokenService()

    async def override_customer_repo():
        return customer_repo

    async def override_vehicle_repo():
        return vehicle_repo

    async def override_service_order_repo():
        return service_order_repo

    async def override_service_item_repo():
        return service_item_repo

    async def override_part_item_repo():
        return part_item_repo

    async def override_catalog_repo():
        return catalog_repo

    async def override_inventory_repo():
        return inventory_repo

    def override_email_sender():
        return email_sender

    def override_approval_token_service():
        return approval_token_service

    def override_settings():
        return settings

    async def override_principal():
        return AuthenticatedPrincipal(
            subject="11144477735",
            role="customer",
            customer_id=str(TEST_CUSTOMER_ID),
            issuer="service-order-auth-lambda/test",
            claims={
                "sub": "11144477735",
                "role": "customer",
                "customer_id": str(TEST_CUSTOMER_ID),
            },
        )

    app.dependency_overrides[get_settings] = override_settings
    app.dependency_overrides[get_customer_repository] = override_customer_repo
    app.dependency_overrides[get_vehicle_repository] = override_vehicle_repo
    app.dependency_overrides[get_service_order_repository] = override_service_order_repo
    app.dependency_overrides[get_service_item_repository] = override_service_item_repo
    app.dependency_overrides[get_part_item_repository] = override_part_item_repo
    app.dependency_overrides[get_catalog_service_repository] = override_catalog_repo
    app.dependency_overrides[get_inventory_part_repository] = override_inventory_repo
    app.dependency_overrides[get_email_sender] = override_email_sender
    app.dependency_overrides[require_customer_or_admin_principal] = override_principal

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield {
            "app": app,
            "client": client,
            "settings": settings,
            "customer_repo": customer_repo,
            "vehicle_repo": vehicle_repo,
            "service_order_repo": service_order_repo,
            "catalog_repo": catalog_repo,
            "inventory_repo": inventory_repo,
            "email_sender": email_sender,
            "approval_token_service": approval_token_service,
        }
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_protected_route_without_token_returns_401():
    app = create_test_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/service-orders/active")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_invalid_customer_token_returns_401():
    settings = Settings(
        DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/db",
        JWT_SECRET="admin-secret-value-with-32-characters",
        CUSTOMER_JWT_SECRET="customer-secret-value-with-32-characters",
        CUSTOMER_JWT_ISSUER="service-order-auth-lambda/test",
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
    app = create_test_app()
    app.dependency_overrides[get_settings] = lambda: settings
    transport = ASGITransport(app=app)
    token = jwt.encode(
        {"sub": "123", "role": "customer", "customer_id": "1", "iss": settings.CUSTOMER_JWT_ISSUER},
        "wrong-secret",
        algorithm="HS256",
    )
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get(
            "/service-orders/active",
            headers={"Authorization": f"Bearer {token}"},
        )
    app.dependency_overrides.clear()
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_customer_token_can_create_and_read_own_service_order(phase3_customer_context):
    customer = Customer(
        id=TEST_CUSTOMER_ID,
        name="Cliente",
        cpf_cnpj="11144477735",
        email="cliente@example.com",
        phone="11999999999",
        is_active=True,
        created_at=utcnow(),
        updated_at=utcnow(),
    )
    vehicle = Vehicle(
        id=uuid4(),
        customer_id=customer.id,
        brand="Toyota",
        model="Corolla",
        year=2023,
        plate="BRA2A34",
        created_at=utcnow(),
        updated_at=utcnow(),
    )
    service = CatalogService(
        id=uuid4(),
        description="Troca de oleo",
        price=150.0,
        created_at=utcnow(),
        updated_at=utcnow(),
    )
    await phase3_customer_context["customer_repo"].save(customer)
    await phase3_customer_context["vehicle_repo"].save(vehicle)
    await phase3_customer_context["catalog_repo"].create(service)

    response = await phase3_customer_context["client"].post(
        "/service-orders",
        json={
            "customer_id": str(customer.id),
            "vehicle_id": str(vehicle.id),
            "service_ids": [str(service.id)],
        },
        headers={"X-Correlation-ID": "corr-phase3-1"},
    )
    assert response.status_code == 201
    assert response.headers["X-Correlation-ID"] == "corr-phase3-1"

    service_order_id = response.json()["service_order_id"]
    detail = await phase3_customer_context["client"].get(
        f"/service-orders/{service_order_id}/status",
        headers={"X-Correlation-ID": "corr-phase3-2"},
    )
    assert detail.status_code == 200
    assert detail.headers["X-Correlation-ID"] == "corr-phase3-2"


@pytest.mark.asyncio
async def test_customer_token_cannot_read_other_customer_service_order(phase3_customer_context):
    order_id = uuid4()
    phase3_customer_context["service_order_repo"].service_orders[order_id] = ServiceOrder(
        id=order_id,
        customer_id=UUID("22222222-2222-2222-2222-222222222222"),
        vehicle_id=uuid4(),
        status=ServiceOrderStatus.WAITING_APPROVAL,
        created_at=utcnow(),
        updated_at=utcnow(),
    )

    response = await phase3_customer_context["client"].get(
        f"/service-orders/{order_id}/status"
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_metrics_endpoint_returns_prometheus_payload():
    app = create_test_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text
