from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from ..entities import Customer


class CustomerRepository(ABC):
    @abstractmethod
    async def save(self, customer: Customer) -> None:
        pass

    @abstractmethod
    async def update(self, customer: Customer) -> None:
        pass

    @abstractmethod
    async def delete(self, customer_id: UUID) -> bool:
        pass

    @abstractmethod
    async def get_by_id(self, customer_id: UUID) -> Customer | None:
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Customer | None:
        pass

    @abstractmethod
    async def get_by_cpf_cnpj(self, cpf_cnpj: str) -> Customer | None:
        pass

    @abstractmethod
    async def list(self) -> list[Customer]:
        pass
