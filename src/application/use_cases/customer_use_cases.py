from uuid import UUID, uuid4

from ...domain.entities import Customer
from ...domain.repositories import CustomerRepository
from ...domain.time import utcnow


class CreateCustomerUseCase:
    def __init__(self, customer_repo: CustomerRepository):
        self.customer_repo = customer_repo

    async def execute(
        self,
        name: str,
        cpf_cnpj: str | None,
        email: str,
        phone: str,
        is_active: bool = True,
    ) -> str:
        now = utcnow()
        if cpf_cnpj:
            existing = await self.customer_repo.get_by_cpf_cnpj(cpf_cnpj)
            if existing is not None:
                raise ValueError("CPF/CNPJ already registered")
        existing_email = await self.customer_repo.get_by_email(email)
        if existing_email is not None:
            raise ValueError("Email already registered")

        customer = Customer(
            id=uuid4(),
            name=name,
            cpf_cnpj=cpf_cnpj,
            email=email,
            phone=phone,
            is_active=is_active,
            created_at=now,
            updated_at=now,
        )
        await self.customer_repo.save(customer)
        return str(customer.id)


class UpdateCustomerUseCase:
    def __init__(self, customer_repo: CustomerRepository):
        self.customer_repo = customer_repo

    async def execute(
        self,
        customer_id: UUID,
        name: str,
        cpf_cnpj: str | None,
        email: str,
        phone: str,
        is_active: bool = True,
    ) -> bool:
        existing = await self.customer_repo.get_by_id(customer_id)
        if existing is None:
            return False

        if cpf_cnpj and cpf_cnpj != existing.cpf_cnpj:
            other = await self.customer_repo.get_by_cpf_cnpj(cpf_cnpj)
            if other is not None and other.id != customer_id:
                raise ValueError("CPF/CNPJ already registered")

        if email != existing.email:
            other_email = await self.customer_repo.get_by_email(email)
            if other_email is not None and other_email.id != customer_id:
                raise ValueError("Email already registered")

        existing.name = name
        existing.cpf_cnpj = cpf_cnpj
        existing.email = email
        existing.phone = phone
        existing.is_active = is_active
        existing.updated_at = utcnow()
        await self.customer_repo.update(existing)
        return True


class DeleteCustomerUseCase:
    def __init__(self, customer_repo: CustomerRepository):
        self.customer_repo = customer_repo

    async def execute(self, customer_id: UUID) -> bool:
        return await self.customer_repo.delete(customer_id)


class GetCustomerUseCase:
    def __init__(self, customer_repo: CustomerRepository):
        self.customer_repo = customer_repo

    async def execute(self, customer_id: UUID) -> Customer | None:
        return await self.customer_repo.get_by_id(customer_id)


class ListCustomersUseCase:
    def __init__(self, customer_repo: CustomerRepository):
        self.customer_repo = customer_repo

    async def execute(self) -> list[Customer]:
        return await self.customer_repo.list()
