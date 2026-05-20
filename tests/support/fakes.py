from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from src.domain.entities import Customer, ServiceOrder
from src.domain.enums import ServiceOrderStatus
from src.domain.errors import ExpiredApprovalTokenError, InvalidApprovalTokenError
from src.domain.repositories import (
    CustomerRepository,
    PartItemRepository,
    ServiceItemRepository,
    ServiceOrderRepository,
    VehicleRepository,
)
from src.domain.services import ApprovalRequestEmailMessage, ApprovalTokenPayload
from src.domain.time import utcnow


class MockCustomerRepository(CustomerRepository):
    def __init__(self):
        self.customers = {}

    async def save(self, customer: Customer) -> None:
        self.customers[customer.id] = customer

    async def update(self, customer: Customer) -> None:
        self.customers[customer.id] = customer

    async def delete(self, customer_id) -> bool:
        return self.customers.pop(customer_id, None) is not None

    async def get_by_id(self, customer_id) -> Customer | None:
        return self.customers.get(customer_id)

    async def get_by_email(self, email: str) -> Customer | None:
        for customer in self.customers.values():
            if customer.email == email:
                return customer
        return None

    async def get_by_cpf_cnpj(self, cpf_cnpj: str) -> Customer | None:
        for customer in self.customers.values():
            if customer.cpf_cnpj == cpf_cnpj:
                return customer
        return None

    async def list(self) -> list[Customer]:
        return list(self.customers.values())


class MockVehicleRepository(VehicleRepository):
    def __init__(self):
        self.vehicles = {}

    async def save(self, vehicle) -> None:
        self.vehicles[vehicle.id] = vehicle

    async def update(self, vehicle) -> None:
        self.vehicles[vehicle.id] = vehicle

    async def delete(self, vehicle_id) -> bool:
        return self.vehicles.pop(vehicle_id, None) is not None

    async def get_by_id(self, vehicle_id) -> None:
        return self.vehicles.get(vehicle_id)

    async def get_by_plate(self, plate: str):
        for vehicle in self.vehicles.values():
            if vehicle.plate == plate:
                return vehicle
        return None

    async def list(self) -> list:
        return list(self.vehicles.values())

    async def list_by_customer_id(self, customer_id):
        return [v for v in self.vehicles.values() if v.customer_id == customer_id]


class MockServiceOrderRepository(ServiceOrderRepository):
    def __init__(self):
        self.service_orders = {}

    async def save(self, service_order: ServiceOrder) -> None:
        self.service_orders[service_order.id] = service_order

    async def update(self, service_order: ServiceOrder) -> None:
        self.service_orders[service_order.id] = service_order

    async def get_by_id(self, service_order_id) -> ServiceOrder | None:
        return self.service_orders.get(service_order_id)

    async def list_all(self) -> list[ServiceOrder]:
        return sorted(self.service_orders.values(), key=lambda order: order.created_at)

    async def update_status(self, service_order_id, status) -> None:
        if service_order_id in self.service_orders:
            service_order = self.service_orders[service_order_id]
            service_order.status = status
            service_order.updated_at = utcnow()

    async def set_started_at(self, service_order_id) -> None:
        if service_order_id in self.service_orders:
            service_order = self.service_orders[service_order_id]
            service_order.started_at = utcnow()

    async def set_finished_at(self, service_order_id) -> None:
        if service_order_id in self.service_orders:
            service_order = self.service_orders[service_order_id]
            service_order.finished_at = utcnow()

    async def get_average_execution_time_seconds(self) -> float | None:
        durations = []
        for service_order in self.service_orders.values():
            if service_order.started_at and service_order.finished_at:
                durations.append(
                    (
                        service_order.finished_at - service_order.started_at
                    ).total_seconds()
                )
        if not durations:
            return None
        return sum(durations) / len(durations)

    async def list_active(self) -> list[ServiceOrder]:
        return [
            service_order
            for service_order in self.service_orders.values()
            if service_order.status
            not in [ServiceOrderStatus.FINISHED, ServiceOrderStatus.DELIVERED]
        ]


class MockServiceItemRepository(ServiceItemRepository):
    async def save(self, service_item) -> None:
        pass

    async def save_many(self, service_items: list) -> None:
        pass

    async def get_by_service_order_id(self, service_order_id):
        return []


class MockPartItemRepository(PartItemRepository):
    async def save(self, part_item) -> None:
        pass

    async def save_many(self, part_items: list) -> None:
        pass

    async def get_by_service_order_id(self, service_order_id):
        return []


class MockEmailSender:
    def __init__(self):
        self.sent = []

    async def send_email(self, to_email: str, subject: str, body: str) -> None:
        self.sent.append(
            {"type": "email", "to": to_email, "subject": subject, "body": body}
        )

    async def send_status_changed(
        self, customer_email: str, service_order_id: str, new_status: str
    ) -> None:
        self.sent.append(
            {
                "type": "status_changed",
                "to": customer_email,
                "service_order_id": service_order_id,
                "new_status": new_status,
            }
        )

    async def send_approval_request(
        self,
        message: ApprovalRequestEmailMessage,
    ) -> None:
        self.sent.append(
            {
                "type": "approval_request",
                "to": message.customer_email,
                "service_order_id": message.service_order_id,
                "total": message.total,
                "summary_lines": message.summary_lines,
                "approve_token": message.approve_token,
                "reject_token": message.reject_token,
            }
        )


class FailingEmailSender(MockEmailSender):
    async def send_email(self, to_email: str, subject: str, body: str) -> None:
        raise RuntimeError("SMTP unavailable")

    async def send_status_changed(
        self, customer_email: str, service_order_id: str, new_status: str
    ) -> None:
        raise RuntimeError("SMTP unavailable")

    async def send_approval_request(
        self,
        message: ApprovalRequestEmailMessage,
    ) -> None:
        raise RuntimeError("SMTP unavailable")


class MockApprovalTokenService:
    def __init__(self):
        self.payloads: dict[str, ApprovalTokenPayload] = {}
        self.counter = 0

    def generate_token(self, service_order_id: UUID, approved: bool) -> str:
        self.counter += 1
        token = f"token-{self.counter}-{service_order_id}-{int(approved)}"
        self.payloads[token] = ApprovalTokenPayload(
            service_order_id=service_order_id,
            approved=approved,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
        )
        return token

    def verify_token(self, token: str) -> ApprovalTokenPayload:
        payload = self.payloads.get(token)
        if payload is None:
            raise InvalidApprovalTokenError("Approval token is invalid")
        if payload.expires_at <= datetime.now(timezone.utc):
            raise ExpiredApprovalTokenError("Approval token has expired")
        return payload

    def add_expired_token(self, service_order_id: UUID, approved: bool) -> str:
        self.counter += 1
        token = f"expired-token-{self.counter}-{service_order_id}-{int(approved)}"
        self.payloads[token] = ApprovalTokenPayload(
            service_order_id=service_order_id,
            approved=approved,
            expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        )
        return token


class MockCatalogServiceRepository:
    def __init__(self):
        self.services = {}

    async def create(self, service) -> None:
        self.services[service.id] = service

    async def update(self, service) -> None:
        self.services[service.id] = service

    async def delete(self, service_id) -> bool:
        return self.services.pop(service_id, None) is not None

    async def get_by_id(self, service_id):
        return self.services.get(service_id)

    async def list(self):
        return list(self.services.values())


class MockInventoryPartRepository:
    def __init__(self):
        self.parts = {}

    async def create(self, part) -> None:
        self.parts[part.id] = part

    async def update(self, part) -> None:
        self.parts[part.id] = part

    async def delete(self, part_id) -> bool:
        return self.parts.pop(part_id, None) is not None

    async def get_by_id(self, part_id):
        return self.parts.get(part_id)

    async def get_by_name(self, name: str):
        for part in self.parts.values():
            if part.name == name:
                return part
        return None

    async def list(self):
        return list(self.parts.values())

    async def decrease_stock(self, part_id, quantity: int) -> bool:
        part = self.parts.get(part_id)
        if part is None:
            return False
        if part.stock_quantity < quantity:
            return False
        part.stock_quantity -= quantity
        return True


class MockUserRepository:
    def __init__(self):
        self.users = {}

    async def save(self, user) -> None:
        self.users[user.id] = user

    async def get_by_email(self, email: str):
        for user in self.users.values():
            if user.email == email:
                return user
        return None
