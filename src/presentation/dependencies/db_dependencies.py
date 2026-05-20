from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...domain.repositories import (
    CatalogServiceRepository,
    CustomerRepository,
    InventoryPartRepository,
    PartItemRepository,
    ServiceItemRepository,
    ServiceOrderRepository,
    UserRepository,
    VehicleRepository,
)
from ...domain.services import (
    AccessTokenService,
    ApprovalTokenService,
    EmailSender,
    PasswordHashService,
)
from ...infrastructure.config.settings import Settings, get_settings
from ...infrastructure.database.repositories.catalog_service_repository import (
    PostgresCatalogServiceRepository,
)
from ...infrastructure.database.repositories.customer_repository import (
    PostgresCustomerRepository,
)
from ...infrastructure.database.repositories.inventory_part_repository import (
    PostgresInventoryPartRepository,
)
from ...infrastructure.database.repositories.part_item_repository import (
    PostgresPartItemRepository,
)
from ...infrastructure.database.repositories.service_item_repository import (
    PostgresServiceItemRepository,
)
from ...infrastructure.database.repositories.service_order_repository import (
    PostgresServiceOrderRepository,
)
from ...infrastructure.database.repositories.user_repository import (
    PostgresUserRepository,
)
from ...infrastructure.database.repositories.vehicle_repository import (
    PostgresVehicleRepository,
)
from ...infrastructure.database.session import DatabaseSession
from ...infrastructure.email import (
    JwtApprovalTokenService,
    JwtService,
    NoopEmailSender,
    PasswordHasher,
    SmtpEmailSender,
)

database_session: DatabaseSession | None = None


def init_database(settings: Settings) -> None:
    global database_session
    database_session = DatabaseSession(settings)


def get_database_session(
    settings: Settings = Depends(get_settings),
) -> DatabaseSession:
    if database_session is None:
        init_database(settings)
    return database_session


async def get_session(
    settings: Settings = Depends(get_settings),
) -> AsyncSession:
    db_session = get_database_session(settings)
    async for session in db_session.get_session():
        yield session


async def get_customer_repository(
    session: AsyncSession = Depends(get_session),
) -> CustomerRepository:
    return PostgresCustomerRepository(session)


async def get_catalog_service_repository(
    session: AsyncSession = Depends(get_session),
) -> CatalogServiceRepository:
    return PostgresCatalogServiceRepository(session)


async def get_inventory_part_repository(
    session: AsyncSession = Depends(get_session),
) -> InventoryPartRepository:
    return PostgresInventoryPartRepository(session)


async def get_vehicle_repository(
    session: AsyncSession = Depends(get_session),
) -> VehicleRepository:
    return PostgresVehicleRepository(session)


async def get_service_order_repository(
    session: AsyncSession = Depends(get_session),
) -> ServiceOrderRepository:
    return PostgresServiceOrderRepository(session)


async def get_service_item_repository(
    session: AsyncSession = Depends(get_session),
) -> ServiceItemRepository:
    return PostgresServiceItemRepository(session)


async def get_part_item_repository(
    session: AsyncSession = Depends(get_session),
) -> PartItemRepository:
    return PostgresPartItemRepository(session)


async def get_user_repository(
    session: AsyncSession = Depends(get_session),
) -> UserRepository:
    return PostgresUserRepository(session)


def get_email_sender(
    settings: Settings = Depends(get_settings),
) -> EmailSender:
    if settings.EMAIL_PROVIDER == "NOOP":
        return NoopEmailSender()
    return SmtpEmailSender(settings)


def get_approval_token_service(
    settings: Settings = Depends(get_settings),
) -> ApprovalTokenService:
    return JwtApprovalTokenService(settings)


def get_jwt_service(
    settings: Settings = Depends(get_settings),
) -> AccessTokenService:
    return JwtService(settings)


def get_password_hasher() -> PasswordHashService:
    return PasswordHasher()
