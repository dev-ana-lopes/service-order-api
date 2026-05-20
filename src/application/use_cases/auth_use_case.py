from uuid import uuid4

from ...domain.entities import User
from ...domain.repositories import UserRepository
from ...domain.services import AccessTokenService, PasswordHashService
from ...domain.time import utcnow
from ..dto.login_dto import LoginDTO


class AuthenticateUserUseCase:
    def __init__(
        self,
        user_repo: UserRepository,
        password_hasher: PasswordHashService,
        jwt_service: AccessTokenService,
    ):
        self.user_repo = user_repo
        self.password_hasher = password_hasher
        self.jwt_service = jwt_service

    async def execute(self, dto: LoginDTO) -> str | None:
        user = await self.user_repo.get_by_email(dto.email)

        if user is None:
            return None

        if not self.password_hasher.verify_password(dto.password, user.password_hash):
            return None

        token = self.jwt_service.create_token(str(user.id), user.email)
        return token


class RegisterUserUseCase:
    def __init__(
        self,
        user_repo: UserRepository,
        password_hasher: PasswordHashService,
    ):
        self.user_repo = user_repo
        self.password_hasher = password_hasher

    async def execute(self, email: str, password: str) -> str:
        user_id = uuid4()
        password_hash = self.password_hasher.hash_password(password)

        user = User(
            id=user_id,
            email=email,
            password_hash=password_hash,
            created_at=utcnow(),
        )

        await self.user_repo.save(user)
        return str(user_id)
