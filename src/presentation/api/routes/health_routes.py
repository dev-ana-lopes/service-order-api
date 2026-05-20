from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from ....infrastructure.config.settings import Settings, get_settings
from ....infrastructure.database.session import DatabaseSession
from ....presentation.dependencies.db_dependencies import get_database_session

router = APIRouter(tags=["health"])

Database = Annotated[DatabaseSession, Depends(get_database_session)]
AppSettings = Annotated[Settings, Depends(get_settings)]


@router.get("/health")
async def health_check(settings: AppSettings) -> dict:
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@router.get("/health/live")
async def live_check(settings: AppSettings) -> dict:
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@router.get("/health/ready")
async def readiness_check(
    database: Database,
    settings: AppSettings,
) -> dict:
    is_ready = await database.ping()
    if not is_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable",
        )

    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "checks": {"database": "ok"},
    }
