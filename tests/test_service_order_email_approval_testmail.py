from __future__ import annotations

from urllib.parse import parse_qs, urlparse
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from src.infrastructure.config.settings import Settings, get_settings
from src.presentation.dependencies.auth_dependencies import get_current_user
from src.presentation.dependencies.db_dependencies import (
    get_catalog_service_repository,
    get_customer_repository,
    get_inventory_part_repository,
    get_part_item_repository,
    get_service_item_repository,
    get_service_order_repository,
    get_vehicle_repository,
)
from tests.support import (
    MockCatalogServiceRepository,
    MockCustomerRepository,
    MockInventoryPartRepository,
    MockPartItemRepository,
    MockServiceItemRepository,
    MockServiceOrderRepository,
    MockVehicleRepository,
    create_test_app,
)
from tests.support.testmail import (
    build_live_test_settings,
    build_testmail_recipient,
    extract_links,
    first_matching_link,
    is_testmail_live_enabled,
    message_text,
    wait_for_testmail_messages,
)


def _create_service_order_payload(customer_email: str) -> dict:
    return {
        "customer_name": "Live User",
        "customer_email": customer_email,
        "customer_phone": "11999999999",
        "vehicle_brand": "Toyota",
        "vehicle_model": "Corolla",
        "vehicle_year": 2022,
        "vehicle_plate": "BRA2A34",
        "services": [{"description": "Revisao completa", "price": 220.0}],
        "parts": [{"name": "Filtro", "price": 35.0, "quantity": 1}],
    }


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.testmail
@pytest.mark.e2e
async def test_service_order_email_approval_flow_with_testmail_live():
    settings = build_live_test_settings()
    if not is_testmail_live_enabled(settings):
        pytest.skip(
            "Testmail live test requires TESTMAIL_ENABLED=true, "
            "TESTMAIL_API_KEY and TESTMAIL_NAMESPACE"
        )

    app = create_test_app()
    customer_repo = MockCustomerRepository()
    vehicle_repo = MockVehicleRepository()
    service_order_repo = MockServiceOrderRepository()
    service_item_repo = MockServiceItemRepository()
    part_item_repo = MockPartItemRepository()
    catalog_service_repo = MockCatalogServiceRepository()
    inventory_part_repo = MockInventoryPartRepository()
    app_settings = Settings(
        **{
            **settings.model_dump(),
            "APP_BASE_URL": "http://testserver",
        }
    )

    async def override_current_user():
        return {"user_id": "test-user"}

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
        return catalog_service_repo

    async def override_inventory_repo():
        return inventory_part_repo

    def override_settings():
        return app_settings

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_customer_repository] = override_customer_repo
    app.dependency_overrides[get_vehicle_repository] = override_vehicle_repo
    app.dependency_overrides[get_service_order_repository] = override_service_order_repo
    app.dependency_overrides[get_service_item_repository] = override_service_item_repo
    app.dependency_overrides[get_part_item_repository] = override_part_item_repo
    app.dependency_overrides[get_catalog_service_repository] = override_catalog_repo
    app.dependency_overrides[get_inventory_part_repository] = override_inventory_repo
    app.dependency_overrides[get_settings] = override_settings

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            tag = f"approval-{uuid4().hex}"
            recipient = build_testmail_recipient(settings, tag)
            create_response = await client.post(
                "/service-orders",
                json=_create_service_order_payload(recipient),
            )

            assert create_response.status_code == 201
            service_order_id = create_response.json()["service_order_id"]

            messages = wait_for_testmail_messages(settings, tag, timeout_seconds=45)
            assert messages, "No approval email received from Testmail before timeout"

            email_text = "\n\n".join(message_text(message) for message in messages)
            links = extract_links(email_text)
            approve_link = first_matching_link(
                links,
                f"/public/service-orders/{service_order_id}/approval?token=",
            )
            assert approve_link, f"Approval link not found in email body: {email_text}"

            parsed_url = urlparse(approve_link)
            token = parse_qs(parsed_url.query)["token"][0]
            approval_response = await client.get(
                parsed_url.path,
                params={"token": token},
            )

            assert approval_response.status_code == 200
            assert approval_response.json()["status"] == "IN_PROGRESS"

            status_response = await client.get(
                f"/public/service-orders/{service_order_id}/status"
            )
            assert status_response.status_code == 200
            assert status_response.json()["status"] == "IN_PROGRESS"
            assert status_response.json()["approval_decision"] == "APPROVED"
    finally:
        app.dependency_overrides.clear()
