from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from ....application.dto.login_dto import LoginDTO
from ....application.use_cases.auth_use_case import (
    AuthenticateUserUseCase,
    RegisterUserUseCase,
)
from ....domain.repositories.user_repository import UserRepository
from ....domain.services import AccessTokenService, PasswordHashService
from ....presentation.dependencies.db_dependencies import (
    get_jwt_service,
    get_password_hasher,
    get_user_repository,
)
from ....presentation.schemas.service_order_schema import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    password_hasher: Annotated[PasswordHashService, Depends(get_password_hasher)],
) -> RegisterResponse:
    existing = await user_repo.get_by_email(request.email)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    use_case = RegisterUserUseCase(user_repo, password_hasher)
    user_id = await use_case.execute(request.email, request.password)
    return RegisterResponse(user_id=user_id)


async def _authenticate(
    email: str,
    password: str,
    user_repo: UserRepository,
    password_hasher: PasswordHashService,
    jwt_service: AccessTokenService,
) -> LoginResponse:
    dto = LoginDTO(email=email, password=password)
    use_case = AuthenticateUserUseCase(user_repo, password_hasher, jwt_service)
    token = await use_case.execute(dto)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    return LoginResponse(access_token=token)


@router.post("/login")
async def login(
    request: LoginRequest,
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    password_hasher: Annotated[PasswordHashService, Depends(get_password_hasher)],
    jwt_service: Annotated[AccessTokenService, Depends(get_jwt_service)],
) -> LoginResponse:
    return await _authenticate(
        request.email,
        request.password,
        user_repo,
        password_hasher,
        jwt_service,
    )


@router.post("/token")
async def token(
    request: Request,
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    password_hasher: Annotated[PasswordHashService, Depends(get_password_hasher)],
    jwt_service: Annotated[AccessTokenService, Depends(get_jwt_service)],
) -> LoginResponse:
    form = await request.form()
    return await _authenticate(
        str(form.get("username", "")),
        str(form.get("password", "")),
        user_repo,
        password_hasher,
        jwt_service,
    )
