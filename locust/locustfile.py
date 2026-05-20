from __future__ import annotations

from uuid import uuid4

from locust import HttpUser, between, task


class WorkshopApiUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self) -> None:
        self.created_order_ids: list[str] = []
        self._authenticate()

    def _authenticate(self) -> None:
        suffix = uuid4().hex[:8]
        email = f"locust-{suffix}@example.com"
        password = "Admin1234"

        self.client.post(
            "/auth/register",
            json={"email": email, "password": password},
            name="/auth/register",
        )
        response = self.client.post(
            "/auth/login",
            json={"email": email, "password": password},
            name="/auth/login",
        )
        response.raise_for_status()
        access_token = response.json()["access_token"]
        self.client.headers.update({"Authorization": f"Bearer {access_token}"})

    def _service_order_payload(self) -> dict:
        suffix = uuid4().hex[:8]
        return {
            "customer_name": f"Locust User {suffix}",
            "customer_email": f"customer-{suffix}@example.com",
            "customer_phone": "11999999999",
            "vehicle_brand": "Toyota",
            "vehicle_model": "Corolla",
            "vehicle_year": 2023,
            "vehicle_plate": f"BRA{suffix[:4].upper()}",
            "services": [{"description": "Revisao completa", "price": 220.0}],
            "parts": [{"name": "Filtro", "price": 35.0, "quantity": 1}],
        }

    @task(3)
    def healthcheck(self) -> None:
        self.client.get("/health", name="/health")

    @task(2)
    def open_service_order(self) -> None:
        response = self.client.post(
            "/service-orders",
            json=self._service_order_payload(),
            name="/service-orders [POST]",
        )
        if response.status_code == 201:
            service_order_id = response.json()["service_order_id"]
            self.created_order_ids.append(service_order_id)
            self.created_order_ids = self.created_order_ids[-20:]

    @task(2)
    def list_active_service_orders(self) -> None:
        self.client.get("/service-orders/active", name="/service-orders/active")

    @task(1)
    def get_service_order_status(self) -> None:
        if not self.created_order_ids:
            self.open_service_order()
            return

        service_order_id = self.created_order_ids[-1]
        self.client.get(
            f"/service-orders/{service_order_id}/status",
            name="/service-orders/{id}/status",
        )
