from abc import ABC, abstractmethod
from uuid import UUID

from ..entities import User


class UserRepository(ABC):
    @abstractmethod
    async def save(self, user: User) -> None:
        pass

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> User | None:
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        pass
