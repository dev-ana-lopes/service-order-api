from dataclasses import dataclass


@dataclass
class CreateServiceOrderDTO:
    customer_id: str | None = None
    vehicle_id: str | None = None
    customer_name: str | None = None
    customer_cpf_cnpj: str | None = None
    customer_email: str | None = None
    customer_phone: str | None = None
    vehicle_brand: str | None = None
    vehicle_model: str | None = None
    vehicle_year: int | None = None
    vehicle_plate: str | None = None
    services: list[dict] | None = None
    parts: list[dict] | None = None
    service_ids: list[str] | None = None
    part_refs: list[dict] | None = None
