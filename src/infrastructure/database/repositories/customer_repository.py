from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.customer import Customer
from src.domain.repositories.customer_repository import CustomerRepository
from src.infrastructure.database.models.customer_model import CustomerModel


class PostgresCustomerRepository(CustomerRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, customer: Customer) -> None:
        model = CustomerModel(
            id=customer.id,
            name=customer.name,
            cpf_cnpj=customer.cpf_cnpj,
            email=customer.email,
            phone=customer.phone,
            is_active=customer.is_active,
            created_at=customer.created_at,
            updated_at=customer.updated_at,
        )
        self.session.add(model)
        await self.session.commit()

    async def update(self, customer: Customer) -> None:
        result = await self.session.execute(
            select(CustomerModel).where(CustomerModel.id == customer.id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return

        model.name = customer.name
        model.cpf_cnpj = customer.cpf_cnpj
        model.email = customer.email
        model.phone = customer.phone
        model.is_active = customer.is_active
        model.updated_at = customer.updated_at
        await self.session.commit()

    async def delete(self, customer_id: UUID) -> bool:
        result = await self.session.execute(
            delete(CustomerModel).where(CustomerModel.id == customer_id)
        )
        await self.session.commit()
        return (result.rowcount or 0) > 0

    async def get_by_id(self, customer_id: UUID) -> Customer | None:
        query = select(CustomerModel).where(CustomerModel.id == customer_id)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return self._to_entity(model)

    async def get_by_email(self, email: str) -> Customer | None:
        query = select(CustomerModel).where(CustomerModel.email == email)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return self._to_entity(model)

    async def get_by_cpf_cnpj(self, cpf_cnpj: str) -> Customer | None:
        query = select(CustomerModel).where(CustomerModel.cpf_cnpj == cpf_cnpj)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return self._to_entity(model)

    async def list(self) -> list[Customer]:
        result = await self.session.execute(
            select(CustomerModel).order_by(CustomerModel.created_at.asc())
        )
        models = result.scalars().all()
        return [self._to_entity(model) for model in models if model is not None]

    def _to_entity(self, model: CustomerModel | None) -> Customer | None:
        if not model:
            return None

        return Customer(
            id=model.id,
            name=model.name,
            cpf_cnpj=model.cpf_cnpj,
            email=model.email,
            phone=model.phone,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
