from datetime import timedelta
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from src.domain.entities import (
    CatalogService,
    Customer,
    InventoryPart,
    ServiceOrder,
    Vehicle,
)
from src.domain.enums import ServiceOrderStatus
from src.domain.time import utcnow
from src.infrastructure.config.settings import Settings, get_settings
from src.domain.contracts.token_verifier import AuthenticatedPrincipal
from src.presentation.dependencies.auth import require_customer_or_admin_principal
from src.presentation.dependencies.db_dependencies import (
    get_approval_token_service,
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


def _build_settings(**overrides) -> Settings:
    base = {
        "DATABASE_URL": "postgresql+asyncpg://user:pass@localhost:5432/db",
        "JWT_SECRET": "super-secret",
        "SMTP_HOST": "mailhog",
        "SMTP_PORT": 1025,
        "SMTP_USE_TLS": False,
        "SMTP_USE_AUTH": False,
        "APP_BASE_URL": "http://testserver",
        "APPROVAL_TOKEN_SECRET": "approval-secret",
    }
    base.update(overrides)
    return Settings(**base)


@pytest_asyncio.fixture
async def service_order_api_context():
    app = create_test_app()
    settings = _build_settings()
    customer_repo = MockCustomerRepository()
    vehicle_repo = MockVehicleRepository()
    service_order_repo = MockServiceOrderRepository()
    service_item_repo = MockServiceItemRepository()
    part_item_repo = MockPartItemRepository()
    catalog_repo = MockCatalogServiceRepository()
    inventory_repo = MockInventoryPartRepository()
    email_sender = MockEmailSender()
    approval_token_service = MockApprovalTokenService()

    async def override_current_user():
        return AuthenticatedPrincipal(
            subject="admin-user",
            role="admin",
            customer_id=None,
            issuer="tests",
            claims={"user_id": "admin-user", "role": "admin"},
        )

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

    app.dependency_overrides[require_customer_or_admin_principal] = override_current_user
    app.dependency_overrides[get_settings] = override_settings
    app.dependency_overrides[get_customer_repository] = override_customer_repo
    app.dependency_overrides[get_vehicle_repository] = override_vehicle_repo
    app.dependency_overrides[get_service_order_repository] = override_service_order_repo
    app.dependency_overrides[get_service_item_repository] = override_service_item_repo
    app.dependency_overrides[get_part_item_repository] = override_part_item_repo
    app.dependency_overrides[get_catalog_service_repository] = override_catalog_repo
    app.dependency_overrides[get_inventory_part_repository] = override_inventory_repo
    app.dependency_overrides[get_email_sender] = override_email_sender
    app.dependency_overrides[
        get_approval_token_service
    ] = override_approval_token_service

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield {
            "app": app,
            "client": client,
            "customer_repo": customer_repo,
            "vehicle_repo": vehicle_repo,
            "service_order_repo": service_order_repo,
            "catalog_repo": catalog_repo,
            "inventory_repo": inventory_repo,
            "email_sender": email_sender,
            "approval_token_service": approval_token_service,
        }

    app.dependency_overrides.clear()


async def _seed_customer_vehicle_and_catalog(context):
    customer = Customer(
        id=uuid4(),
        name="Cliente",
        cpf_cnpj="11144477735",
        email="cliente@example.com",
        phone="11999999999",
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
    part = InventoryPart(
        id=uuid4(),
        name="Filtro",
        unit_price=50.0,
        stock_quantity=10,
        created_at=utcnow(),
        updated_at=utcnow(),
    )
    await context["customer_repo"].save(customer)
    await context["vehicle_repo"].save(vehicle)
    await context["catalog_repo"].create(service)
    await context["inventory_repo"].create(part)
    return customer, vehicle, service, part


@pytest.mark.asyncio
async def test_open_service_order_returns_identifier_budget_and_email(
    service_order_api_context,
):
    customer, vehicle, service, part = await _seed_customer_vehicle_and_catalog(
        service_order_api_context
    )

    response = await service_order_api_context["client"].post(
        "/service-orders",
        json={
            "customer_id": str(customer.id),
            "vehicle_id": str(vehicle.id),
            "service_ids": [str(service.id)],
            "part_refs": [{"part_id": str(part.id), "quantity": 2}],
        },
    )

    assert response.status_code == 201
    service_order_id = response.json()["service_order_id"]
    assert service_order_id
    assert service_order_api_context["inventory_repo"].parts[part.id].stock_quantity == 8
    assert any(
        message["type"] == "approval_request"
        and message["service_order_id"] == service_order_id
        and message["total"] == 250.0
        for message in service_order_api_context["email_sender"].sent
    )

    detail = await service_order_api_context["client"].get(
        f"/service-orders/{service_order_id}"
    )
    assert detail.status_code == 200
    assert detail.json()["status"] == "WAITING_APPROVAL"
    assert detail.json()["budget_total"] == 250.0


@pytest.mark.asyncio
async def test_manual_approval_and_rejection_update_domain_consistently(
    service_order_api_context,
):
    customer, vehicle, service, part = await _seed_customer_vehicle_and_catalog(
        service_order_api_context
    )
    create_response = await service_order_api_context["client"].post(
        "/service-orders",
        json={
            "customer_id": str(customer.id),
            "vehicle_id": str(vehicle.id),
            "service_ids": [str(service.id)],
            "part_refs": [{"part_id": str(part.id), "quantity": 1}],
        },
    )
    order_id = create_response.json()["service_order_id"]

    approve = await service_order_api_context["client"].post(
        f"/service-orders/{order_id}/approval",
        json={"approved": True},
    )
    assert approve.status_code == 200
    assert approve.json()["status"] == "IN_PROGRESS"

    second_create = await service_order_api_context["client"].post(
        "/service-orders",
        json={
            "customer_id": str(customer.id),
            "vehicle_id": str(vehicle.id),
            "service_ids": [str(service.id)],
            "part_refs": [{"part_id": str(part.id), "quantity": 1}],
        },
    )
    second_order_id = second_create.json()["service_order_id"]
    reject = await service_order_api_context["client"].post(
        f"/service-orders/{second_order_id}/approval",
        json={
            "approved": False,
            "rejection_reason": "Cliente pediu nova analise",
        },
    )
    assert reject.status_code == 200
    assert reject.json() == {
        "success": True,
        "status": "DIAGNOSIS",
        "decision": "REJECTED",
        "rejection_reason": "Cliente pediu nova analise",
    }

    status_response = await service_order_api_context["client"].get(
        f"/service-orders/{second_order_id}/status"
    )
    assert status_response.status_code == 200
    assert status_response.json() == {
        "status": "DIAGNOSIS",
        "approval_decision": "REJECTED",
        "rejection_reason": "Cliente pediu nova analise",
    }


@pytest.mark.asyncio
async def test_public_approval_supports_email_click_and_external_notification(
    service_order_api_context,
):
    customer, vehicle, service, part = await _seed_customer_vehicle_and_catalog(
        service_order_api_context
    )

    approve_response = await service_order_api_context["client"].post(
        "/service-orders",
        json={
            "customer_id": str(customer.id),
            "vehicle_id": str(vehicle.id),
            "service_ids": [str(service.id)],
            "part_refs": [{"part_id": str(part.id), "quantity": 1}],
        },
    )
    approve_order_id = approve_response.json()["service_order_id"]
    approve_message = next(
        message
        for message in service_order_api_context["email_sender"].sent
        if message["service_order_id"] == approve_order_id
    )

    public_get = await service_order_api_context["client"].get(
        f"/public/service-orders/{approve_order_id}/approval",
        params={"token": approve_message["approve_token"]},
    )
    assert public_get.status_code == 200
    assert public_get.json()["decision"] == "APPROVED"
    public_approve_status = await service_order_api_context["client"].get(
        f"/public/service-orders/{approve_order_id}/status"
    )
    assert public_approve_status.status_code == 200
    assert public_approve_status.json() == {
        "status": "IN_PROGRESS",
        "approval_decision": "APPROVED",
        "rejection_reason": None,
    }

    reject_response = await service_order_api_context["client"].post(
        "/service-orders",
        json={
            "customer_id": str(customer.id),
            "vehicle_id": str(vehicle.id),
            "service_ids": [str(service.id)],
            "part_refs": [{"part_id": str(part.id), "quantity": 1}],
        },
    )
    reject_order_id = reject_response.json()["service_order_id"]
    reject_message = [
        message
        for message in service_order_api_context["email_sender"].sent
        if message["service_order_id"] == reject_order_id
    ][-1]

    public_post = await service_order_api_context["client"].post(
        f"/public/service-orders/{reject_order_id}/approval",
        json={"token": reject_message["reject_token"]},
    )
    assert public_post.status_code == 200
    assert public_post.json()["decision"] == "REJECTED"
    public_reject_status = await service_order_api_context["client"].get(
        f"/public/service-orders/{reject_order_id}/status"
    )
    assert public_reject_status.status_code == 200
    assert public_reject_status.json() == {
        "status": "DIAGNOSIS",
        "approval_decision": "REJECTED",
        "rejection_reason": None,
    }


@pytest.mark.asyncio
async def test_active_list_orders_by_priority_and_hides_finished_and_delivered(
    service_order_api_context,
):
    repo = service_order_api_context["service_order_repo"]
    base_time = utcnow()
    orders = [
        ServiceOrder(
            id=uuid4(),
            customer_id=uuid4(),
            vehicle_id=uuid4(),
            status=ServiceOrderStatus.RECEIVED,
            created_at=base_time - timedelta(minutes=10),
            updated_at=base_time - timedelta(minutes=10),
        ),
        ServiceOrder(
            id=uuid4(),
            customer_id=uuid4(),
            vehicle_id=uuid4(),
            status=ServiceOrderStatus.DIAGNOSIS,
            created_at=base_time - timedelta(minutes=9),
            updated_at=base_time - timedelta(minutes=9),
        ),
        ServiceOrder(
            id=uuid4(),
            customer_id=uuid4(),
            vehicle_id=uuid4(),
            status=ServiceOrderStatus.WAITING_APPROVAL,
            created_at=base_time - timedelta(minutes=20),
            updated_at=base_time - timedelta(minutes=20),
        ),
        ServiceOrder(
            id=uuid4(),
            customer_id=uuid4(),
            vehicle_id=uuid4(),
            status=ServiceOrderStatus.IN_PROGRESS,
            created_at=base_time - timedelta(minutes=8),
            updated_at=base_time - timedelta(minutes=8),
        ),
        ServiceOrder(
            id=uuid4(),
            customer_id=uuid4(),
            vehicle_id=uuid4(),
            status=ServiceOrderStatus.FINISHED,
            created_at=base_time - timedelta(minutes=30),
            updated_at=base_time - timedelta(minutes=30),
        ),
        ServiceOrder(
            id=uuid4(),
            customer_id=uuid4(),
            vehicle_id=uuid4(),
            status=ServiceOrderStatus.DELIVERED,
            created_at=base_time - timedelta(minutes=40),
            updated_at=base_time - timedelta(minutes=40),
        ),
    ]
    for order in orders:
        await repo.save(order)

    response = await service_order_api_context["client"].get("/service-orders/active")

    assert response.status_code == 200
    assert [item["status"] for item in response.json()] == [
        "IN_PROGRESS",
        "WAITING_APPROVAL",
        "DIAGNOSIS",
        "RECEIVED",
    ]


@pytest.mark.asyncio
async def test_update_status_to_waiting_approval_resends_budget_email(
    service_order_api_context,
):
    customer = Customer(
        id=uuid4(),
        name="Maria",
        cpf_cnpj=None,
        email="maria@example.com",
        phone="11999999999",
        created_at=utcnow(),
        updated_at=utcnow(),
    )
    order = ServiceOrder(
        id=uuid4(),
        customer_id=customer.id,
        vehicle_id=uuid4(),
        status=ServiceOrderStatus.DIAGNOSIS,
        created_at=utcnow(),
        updated_at=utcnow(),
    )
    await service_order_api_context["customer_repo"].save(customer)
    await service_order_api_context["service_order_repo"].save(order)

    response = await service_order_api_context["client"].patch(
        f"/service-orders/{order.id}/status",
        json={"status": "WAITING_APPROVAL"},
    )

    assert response.status_code == 200
    assert any(
        message["type"] == "approval_request" and message["to"] == "maria@example.com"
        for message in service_order_api_context["email_sender"].sent
    )
