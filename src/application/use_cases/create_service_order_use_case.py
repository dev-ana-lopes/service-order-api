import logging
from uuid import UUID, uuid4

from ...domain.entities import Customer, PartItem, ServiceItem, ServiceOrder, Vehicle
from ...domain.enums import ServiceOrderStatus
from ...domain.repositories import (
    CatalogServiceRepository,
    CustomerRepository,
    InventoryPartRepository,
    PartItemRepository,
    ServiceItemRepository,
    ServiceOrderRepository,
    VehicleRepository,
)
from ...domain.services import ApprovalTokenService, EmailSender
from ...domain.time import utcnow
from ..dto.create_service_order_dto import CreateServiceOrderDTO
from .send_approval_request_email_use_case import SendApprovalRequestEmailUseCase

logger = logging.getLogger(__name__)


class CreateServiceOrderUseCase:
    def __init__(
        self,
        customer_repo: CustomerRepository,
        vehicle_repo: VehicleRepository,
        service_order_repo: ServiceOrderRepository,
        service_item_repo: ServiceItemRepository,
        part_item_repo: PartItemRepository,
        catalog_service_repo: CatalogServiceRepository,
        inventory_part_repo: InventoryPartRepository,
        email_sender: EmailSender,
        approval_token_service: ApprovalTokenService,
    ):
        self.customer_repo = customer_repo
        self.vehicle_repo = vehicle_repo
        self.service_order_repo = service_order_repo
        self.service_item_repo = service_item_repo
        self.part_item_repo = part_item_repo
        self.catalog_service_repo = catalog_service_repo
        self.inventory_part_repo = inventory_part_repo
        self.send_approval_request_email_use_case = SendApprovalRequestEmailUseCase(
            email_sender,
            approval_token_service,
        )

    async def execute(self, dto: CreateServiceOrderDTO) -> str:
        now = utcnow()
        customer = await self._resolve_customer(dto, now)
        vehicle = await self._resolve_vehicle(dto, customer.id, now)

        service_order_id = uuid4()
        service_items: list[ServiceItem] = []
        if dto.service_ids:
            for service_id in dto.service_ids:
                catalog_service = await self.catalog_service_repo.get_by_id(
                    UUID(service_id)
                )
                if catalog_service is None:
                    raise ValueError(f"Service not found: {service_id}")
                service_items.append(
                    ServiceItem(
                        id=uuid4(),
                        service_order_id=service_order_id,
                        description=catalog_service.description,
                        price=float(catalog_service.price),
                        created_at=now,
                    )
                )
        else:
            for service in dto.services or []:
                service_items.append(
                    ServiceItem(
                        id=uuid4(),
                        service_order_id=service_order_id,
                        description=service["description"],
                        price=float(service["price"]),
                        created_at=now,
                    )
                )

        part_items: list[PartItem] = []
        if dto.part_refs:
            for part in dto.part_refs:
                part_id = UUID(part["part_id"])
                quantity = int(part["quantity"])
                inventory_part = await self.inventory_part_repo.get_by_id(part_id)
                if inventory_part is None:
                    raise ValueError(f"Part not found: {part_id}")
                ok = await self.inventory_part_repo.decrease_stock(part_id, quantity)
                if not ok:
                    raise ValueError(
                        f"Insufficient stock for part {inventory_part.name}"
                    )
                part_items.append(
                    PartItem(
                        id=uuid4(),
                        service_order_id=service_order_id,
                        name=inventory_part.name,
                        price=float(inventory_part.unit_price),
                        quantity=quantity,
                        created_at=now,
                    )
                )
        else:
            for part in dto.parts or []:
                part_items.append(
                    PartItem(
                        id=uuid4(),
                        service_order_id=service_order_id,
                        name=part["name"],
                        price=float(part["price"]),
                        quantity=int(part["quantity"]),
                        created_at=now,
                    )
                )

        service_order = ServiceOrder(
            id=service_order_id,
            customer_id=customer.id,
            vehicle_id=vehicle.id,
            status=ServiceOrderStatus.WAITING_APPROVAL,
            created_at=now,
            updated_at=now,
            service_items=service_items,
            part_items=part_items,
        )

        await self.service_order_repo.save(service_order)

        try:
            await self.send_approval_request_email_use_case.execute(
                customer.email,
                service_order,
            )
        except Exception:
            logger.exception(
                "Failed to send approval request email for service order %s",
                service_order_id,
            )

        return str(service_order_id)

    async def _resolve_customer(
        self,
        dto: CreateServiceOrderDTO,
        now,
    ) -> Customer:
        if dto.customer_id:
            customer = await self.customer_repo.get_by_id(UUID(dto.customer_id))
            if customer is None:
                raise LookupError("Customer not found")
            return customer

        if not all([dto.customer_name, dto.customer_email, dto.customer_phone]):
            raise ValueError(
                "customer_id or customer_name/customer_email/"
                "customer_phone must be provided"
            )

        customer = None
        if dto.customer_cpf_cnpj:
            customer = await self.customer_repo.get_by_cpf_cnpj(dto.customer_cpf_cnpj)
        if customer is None and dto.customer_email:
            customer = await self.customer_repo.get_by_email(dto.customer_email)

        if customer is None:
            customer = Customer(
                id=uuid4(),
                name=dto.customer_name,
                cpf_cnpj=dto.customer_cpf_cnpj,
                email=dto.customer_email,
                phone=dto.customer_phone,
                created_at=now,
                updated_at=now,
            )
            await self.customer_repo.save(customer)
            return customer

        customer.name = dto.customer_name
        customer.email = dto.customer_email
        customer.phone = dto.customer_phone
        customer.cpf_cnpj = dto.customer_cpf_cnpj or customer.cpf_cnpj
        customer.updated_at = now
        await self.customer_repo.update(customer)
        return customer

    async def _resolve_vehicle(
        self,
        dto: CreateServiceOrderDTO,
        customer_id: UUID,
        now,
    ) -> Vehicle:
        if dto.vehicle_id:
            vehicle = await self.vehicle_repo.get_by_id(UUID(dto.vehicle_id))
            if vehicle is None:
                raise LookupError("Vehicle not found")
            if vehicle.customer_id != customer_id:
                raise ValueError("Vehicle does not belong to the informed customer")
            return vehicle

        if not all(
            [dto.vehicle_brand, dto.vehicle_model, dto.vehicle_year, dto.vehicle_plate]
        ):
            raise ValueError(
                "vehicle_id or vehicle_brand/vehicle_model/"
                "vehicle_year/vehicle_plate must be provided"
            )

        vehicle = await self.vehicle_repo.get_by_plate(dto.vehicle_plate)
        if vehicle is None:
            vehicle = Vehicle(
                id=uuid4(),
                customer_id=customer_id,
                brand=dto.vehicle_brand,
                model=dto.vehicle_model,
                year=dto.vehicle_year,
                plate=dto.vehicle_plate,
                created_at=now,
                updated_at=now,
            )
            await self.vehicle_repo.save(vehicle)
            return vehicle

        vehicle.customer_id = customer_id
        vehicle.brand = dto.vehicle_brand
        vehicle.model = dto.vehicle_model
        vehicle.year = dto.vehicle_year
        vehicle.plate = dto.vehicle_plate
        vehicle.updated_at = now
        await self.vehicle_repo.update(vehicle)
        return vehicle
