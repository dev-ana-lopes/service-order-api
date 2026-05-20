from uuid import UUID, uuid4

from ...domain.entities import Vehicle
from ...domain.repositories import CustomerRepository, VehicleRepository
from ...domain.time import utcnow


class CreateVehicleUseCase:
    def __init__(
        self,
        vehicle_repo: VehicleRepository,
        customer_repo: CustomerRepository,
    ):
        self.vehicle_repo = vehicle_repo
        self.customer_repo = customer_repo

    async def execute(
        self,
        customer_id: UUID,
        brand: str,
        model: str,
        year: int,
        plate: str,
    ) -> str:
        customer = await self.customer_repo.get_by_id(customer_id)
        if customer is None:
            raise LookupError("Customer not found")
        existing = await self.vehicle_repo.get_by_plate(plate)
        if existing is not None:
            raise ValueError("Vehicle plate already registered")
        now = utcnow()
        vehicle = Vehicle(
            id=uuid4(),
            customer_id=customer_id,
            brand=brand,
            model=model,
            year=year,
            plate=plate,
            created_at=now,
            updated_at=now,
        )
        await self.vehicle_repo.save(vehicle)
        return str(vehicle.id)


class UpdateVehicleUseCase:
    def __init__(
        self,
        vehicle_repo: VehicleRepository,
        customer_repo: CustomerRepository,
    ):
        self.vehicle_repo = vehicle_repo
        self.customer_repo = customer_repo

    async def execute(
        self,
        vehicle_id: UUID,
        customer_id: UUID,
        brand: str,
        model: str,
        year: int,
        plate: str,
    ) -> bool:
        existing = await self.vehicle_repo.get_by_id(vehicle_id)
        if existing is None:
            return False
        customer = await self.customer_repo.get_by_id(customer_id)
        if customer is None:
            raise LookupError("Customer not found")
        if plate != existing.plate:
            other = await self.vehicle_repo.get_by_plate(plate)
            if other is not None and other.id != vehicle_id:
                raise ValueError("Vehicle plate already registered")

        existing.customer_id = customer_id
        existing.brand = brand
        existing.model = model
        existing.year = year
        existing.plate = plate
        existing.updated_at = utcnow()
        await self.vehicle_repo.update(existing)
        return True


class DeleteVehicleUseCase:
    def __init__(self, vehicle_repo: VehicleRepository):
        self.vehicle_repo = vehicle_repo

    async def execute(self, vehicle_id: UUID) -> bool:
        return await self.vehicle_repo.delete(vehicle_id)


class GetVehicleUseCase:
    def __init__(self, vehicle_repo: VehicleRepository):
        self.vehicle_repo = vehicle_repo

    async def execute(self, vehicle_id: UUID) -> Vehicle | None:
        return await self.vehicle_repo.get_by_id(vehicle_id)


class ListVehiclesUseCase:
    def __init__(self, vehicle_repo: VehicleRepository):
        self.vehicle_repo = vehicle_repo

    async def execute(self, customer_id: UUID | None = None) -> list[Vehicle]:
        if customer_id is None:
            return await self.vehicle_repo.list()
        return await self.vehicle_repo.list_by_customer_id(customer_id)
