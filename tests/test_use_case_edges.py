from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from src.application.dto.create_service_order_dto import CreateServiceOrderDTO
from src.application.use_cases.apply_service_order_approval_decision_use_case import (
    ApplyServiceOrderApprovalDecisionUseCase,
)
from src.application.use_cases.catalog_use_cases import (
    CreateCatalogServiceUseCase,
    CreateInventoryPartUseCase,
    DeleteCatalogServiceUseCase,
    DeleteInventoryPartUseCase,
    GetCatalogServiceUseCase,
    GetInventoryPartUseCase,
    ListCatalogServicesUseCase,
    ListInventoryPartsUseCase,
    UpdateCatalogServiceUseCase,
    UpdateInventoryPartUseCase,
)
from src.application.use_cases.create_service_order_use_case import (
    CreateServiceOrderUseCase,
)
from src.application.use_cases.customer_use_cases import (
    CreateCustomerUseCase,
    DeleteCustomerUseCase,
    GetCustomerUseCase,
    ListCustomersUseCase,
    UpdateCustomerUseCase,
)
from src.application.use_cases.update_service_order_status_use_case import (
    UpdateServiceOrderStatusUseCase,
)
from src.domain.entities import Customer, ServiceOrder, Vehicle
from src.domain.enums import ServiceOrderStatus
from src.domain.time import utcnow
from src.presentation.dependencies.auth_dependencies import get_current_user
from src.presentation.dependencies.db_dependencies import (
    get_approval_token_service,
    get_customer_repository,
    get_email_sender,
    get_service_order_repository,
)
from tests.support import (
    FailingEmailSender,
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


@pytest.mark.asyncio
async def test_create_service_order_use_case_supports_legacy_inline_payload():
    customer_repo = MockCustomerRepository()
    vehicle_repo = MockVehicleRepository()
    service_order_repo = MockServiceOrderRepository()
    service_item_repo = MockServiceItemRepository()
    part_item_repo = MockPartItemRepository()
    catalog_repo = MockCatalogServiceRepository()
    inventory_repo = MockInventoryPartRepository()
    email_sender = MockEmailSender()
    approval_token_service = MockApprovalTokenService()

    existing_customer = Customer(
        id=uuid4(),
        name="Antigo",
        cpf_cnpj="11144477735",
        email="cliente@example.com",
        phone="1111",
        created_at=utcnow(),
        updated_at=utcnow(),
    )
    existing_vehicle = Vehicle(
        id=uuid4(),
        customer_id=existing_customer.id,
        brand="VW",
        model="Gol",
        year=2018,
        plate="BRA2A34",
        created_at=utcnow(),
        updated_at=utcnow(),
    )
    await customer_repo.save(existing_customer)
    await vehicle_repo.save(existing_vehicle)

    use_case = CreateServiceOrderUseCase(
        customer_repo,
        vehicle_repo,
        service_order_repo,
        service_item_repo,
        part_item_repo,
        catalog_repo,
        inventory_repo,
        email_sender,
        approval_token_service,
    )
    service_order_id = await use_case.execute(
        CreateServiceOrderDTO(
            customer_name="Cliente Atualizado",
            customer_cpf_cnpj="11144477735",
            customer_email="cliente@example.com",
            customer_phone="11999999999",
            vehicle_brand="Toyota",
            vehicle_model="Yaris",
            vehicle_year=2024,
            vehicle_plate="BRA2A34",
            services=[{"description": "Diagnostico", "price": 100.0}],
            parts=[{"name": "Filtro", "price": 25.0, "quantity": 2}],
        )
    )

    service_order = await service_order_repo.get_by_id(UUID(service_order_id))
    assert service_order is not None
    assert service_order.budget_total == 150.0
    assert existing_customer.name == "Cliente Atualizado"
    assert existing_vehicle.model == "Yaris"


@pytest.mark.asyncio
async def test_create_service_order_use_case_is_best_effort_when_email_fails():
    customer_repo = MockCustomerRepository()
    vehicle_repo = MockVehicleRepository()
    service_order_repo = MockServiceOrderRepository()
    service_item_repo = MockServiceItemRepository()
    part_item_repo = MockPartItemRepository()
    catalog_repo = MockCatalogServiceRepository()
    inventory_repo = MockInventoryPartRepository()
    approval_token_service = MockApprovalTokenService()

    use_case = CreateServiceOrderUseCase(
        customer_repo,
        vehicle_repo,
        service_order_repo,
        service_item_repo,
        part_item_repo,
        catalog_repo,
        inventory_repo,
        FailingEmailSender(),
        approval_token_service,
    )

    service_order_id = await use_case.execute(
        CreateServiceOrderDTO(
            customer_name="Cliente Best Effort",
            customer_email="cliente-best-effort@example.com",
            customer_phone="11999999999",
            vehicle_brand="Toyota",
            vehicle_model="Corolla",
            vehicle_year=2024,
            vehicle_plate="BRA2A34",
            services=[{"description": "Diagnostico", "price": 100.0}],
            parts=[{"name": "Filtro", "price": 25.0, "quantity": 2}],
        )
    )

    service_order = await service_order_repo.get_by_id(UUID(service_order_id))
    assert service_order is not None
    assert service_order.status == ServiceOrderStatus.WAITING_APPROVAL


@pytest.mark.asyncio
async def test_create_service_order_use_case_validates_missing_context_and_stock():
    customer_repo = MockCustomerRepository()
    vehicle_repo = MockVehicleRepository()
    service_order_repo = MockServiceOrderRepository()
    service_item_repo = MockServiceItemRepository()
    part_item_repo = MockPartItemRepository()
    catalog_repo = MockCatalogServiceRepository()
    inventory_repo = MockInventoryPartRepository()
    email_sender = MockEmailSender()
    approval_token_service = MockApprovalTokenService()

    use_case = CreateServiceOrderUseCase(
        customer_repo,
        vehicle_repo,
        service_order_repo,
        service_item_repo,
        part_item_repo,
        catalog_repo,
        inventory_repo,
        email_sender,
        approval_token_service,
    )

    with pytest.raises(ValueError):
        await use_case.execute(
            CreateServiceOrderDTO(service_ids=["00000000-0000-0000-0000-000000000001"])
        )

    customer = Customer(
        id=uuid4(),
        name="Cliente",
        cpf_cnpj=None,
        email="cliente2@example.com",
        phone="123",
        created_at=utcnow(),
        updated_at=utcnow(),
    )
    foreign_vehicle = Vehicle(
        id=uuid4(),
        customer_id=uuid4(),
        brand="Ford",
        model="Ka",
        year=2020,
        plate="ABC1234",
        created_at=utcnow(),
        updated_at=utcnow(),
    )
    await customer_repo.save(customer)
    await vehicle_repo.save(foreign_vehicle)

    with pytest.raises(ValueError):
        await use_case.execute(
            CreateServiceOrderDTO(
                customer_id=str(customer.id),
                vehicle_id=str(foreign_vehicle.id),
                services=[{"description": "Troca", "price": 10.0}],
            )
        )


@pytest.mark.asyncio
async def test_approval_and_status_update_are_best_effort_when_email_fails():
    customer_repo = MockCustomerRepository()
    service_order_repo = MockServiceOrderRepository()
    approval_token_service = MockApprovalTokenService()
    email_sender = FailingEmailSender()
    customer = Customer(
        id=uuid4(),
        name="Cliente",
        cpf_cnpj=None,
        email="cliente@example.com",
        phone="11999999999",
        created_at=utcnow(),
        updated_at=utcnow(),
    )
    service_order = ServiceOrder(
        id=uuid4(),
        customer_id=customer.id,
        vehicle_id=uuid4(),
        status=ServiceOrderStatus.WAITING_APPROVAL,
        created_at=utcnow(),
        updated_at=utcnow(),
    )

    await customer_repo.save(customer)
    await service_order_repo.save(service_order)

    approval_use_case = ApplyServiceOrderApprovalDecisionUseCase(
        service_order_repo,
        customer_repo,
        email_sender,
    )
    approval_status = await approval_use_case.execute(service_order.id, approved=False)
    assert approval_status == ServiceOrderStatus.DIAGNOSIS

    update_use_case = UpdateServiceOrderStatusUseCase(
        service_order_repo,
        customer_repo,
        email_sender,
        approval_token_service,
    )
    updated_status = await update_use_case.execute(
        service_order.id,
        ServiceOrderStatus.WAITING_APPROVAL.value,
    )
    assert updated_status == ServiceOrderStatus.WAITING_APPROVAL


@pytest.mark.asyncio
async def test_customer_use_cases_cover_crud_lifecycle():
    repo = MockCustomerRepository()
    create_use_case = CreateCustomerUseCase(repo)
    customer_id = await create_use_case.execute(
        "Maria",
        "11144477735",
        "maria@example.com",
        "11999999999",
    )

    list_use_case = ListCustomersUseCase(repo)
    assert len(await list_use_case.execute()) == 1

    update_use_case = UpdateCustomerUseCase(repo)
    assert (
        await update_use_case.execute(
            UUID(customer_id),
            "Maria Silva",
            "11144477735",
            "maria@example.com",
            "11888888888",
        )
        is True
    )

    get_use_case = GetCustomerUseCase(repo)
    customer = await get_use_case.execute(UUID(customer_id))
    assert customer is not None
    assert customer.name == "Maria Silva"

    delete_use_case = DeleteCustomerUseCase(repo)
    assert await delete_use_case.execute(UUID(customer_id)) is True


@pytest.mark.asyncio
async def test_catalog_use_cases_cover_crud_lifecycle():
    service_repo = MockCatalogServiceRepository()
    part_repo = MockInventoryPartRepository()

    service_id = await CreateCatalogServiceUseCase(service_repo).execute(
        "Alinhamento", 90.0
    )
    part_id = await CreateInventoryPartUseCase(part_repo).execute("Pastilha", 120.0, 3)

    assert len(await ListCatalogServicesUseCase(service_repo).execute()) == 1
    assert len(await ListInventoryPartsUseCase(part_repo).execute()) == 1

    assert await UpdateCatalogServiceUseCase(service_repo).execute(
        UUID(service_id), "Alinhamento 3D", 110.0
    )
    assert await UpdateInventoryPartUseCase(part_repo).execute(
        UUID(part_id), "Pastilha Premium", 150.0, 5
    )

    assert (
        await GetCatalogServiceUseCase(service_repo).execute(UUID(service_id))
    ).description == "Alinhamento 3D"
    assert (
        await GetInventoryPartUseCase(part_repo).execute(UUID(part_id))
    ).name == "Pastilha Premium"

    assert (
        await DeleteCatalogServiceUseCase(service_repo).execute(UUID(service_id)) is True
    )
    assert await DeleteInventoryPartUseCase(part_repo).execute(UUID(part_id)) is True


@pytest_asyncio.fixture
async def public_api_context():
    app = create_test_app()
    customer_repo = MockCustomerRepository()
    service_order_repo = MockServiceOrderRepository()
    email_sender = MockEmailSender()
    approval_token_service = MockApprovalTokenService()

    async def override_current_user():
        return {"user_id": "admin"}

    async def override_customer_repo():
        return customer_repo

    async def override_service_order_repo():
        return service_order_repo

    def override_email_sender():
        return email_sender

    def override_token_service():
        return approval_token_service

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_customer_repository] = override_customer_repo
    app.dependency_overrides[get_service_order_repository] = override_service_order_repo
    app.dependency_overrides[get_email_sender] = override_email_sender
    app.dependency_overrides[get_approval_token_service] = override_token_service

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield {
            "app": app,
            "client": client,
            "customer_repo": customer_repo,
            "service_order_repo": service_order_repo,
            "approval_token_service": approval_token_service,
        }

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_public_approval_route_rejects_invalid_and_reused_tokens(
    public_api_context,
):
    customer = Customer(
        id=uuid4(),
        name="Cliente",
        cpf_cnpj=None,
        email="cliente@example.com",
        phone="11999999999",
        created_at=utcnow(),
        updated_at=utcnow(),
    )
    order = ServiceOrder(
        id=uuid4(),
        customer_id=customer.id,
        vehicle_id=uuid4(),
        status=ServiceOrderStatus.WAITING_APPROVAL,
        created_at=utcnow(),
        updated_at=utcnow(),
    )
    await public_api_context["customer_repo"].save(customer)
    await public_api_context["service_order_repo"].save(order)

    invalid = await public_api_context["client"].get(
        f"/public/service-orders/{order.id}/approval",
        params={"token": "invalid"},
    )
    assert invalid.status_code == 400

    token = public_api_context["approval_token_service"].generate_token(order.id, True)
    first = await public_api_context["client"].get(
        f"/public/service-orders/{order.id}/approval",
        params={"token": token},
    )
    second = await public_api_context["client"].get(
        f"/public/service-orders/{order.id}/approval",
        params={"token": token},
    )

    assert first.status_code == 200
    assert second.status_code == 409
