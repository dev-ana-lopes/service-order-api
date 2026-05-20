from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.user import User
from src.domain.repositories.user_repository import UserRepository

from ..models.user_model import UserModel


class PostgresUserRepository(UserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, user: User) -> None:
        model = UserModel(
            id=user.id,
            email=user.email,
            password_hash=user.password_hash,
            created_at=user.created_at,
        )
        self.session.add(model)
        await self.session.commit()

    async def get_by_id(self, user_id: UUID) -> User | None:
        query = select(UserModel).where(UserModel.id == user_id)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return User(
            id=model.id,
            email=model.email,
            password_hash=model.password_hash,
            created_at=model.created_at,
        )

    async def get_by_email(self, email: str) -> User | None:
        query = select(UserModel).where(UserModel.email == email)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return User(
            id=model.id,
            email=model.email,
            password_hash=model.password_hash,
            created_at=model.created_at,
        )
