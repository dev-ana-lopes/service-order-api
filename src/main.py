import logging
from contextlib import asynccontextmanager
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .infrastructure.config.settings import Settings, get_settings
from .infrastructure.logging import configure_logging
from .infrastructure.observability.metrics import REQUEST_COUNTER, REQUEST_DURATION
from .infrastructure.observability.tracing import configure_telemetry
from .presentation.api.exception_handlers import register_exception_handlers
from .presentation.api.routes import (
    auth_router,
    catalog_router,
    customer_router,
    health_router,
    metrics_router,
    observability_router,
    public_router,
    service_order_router,
    vehicle_router,
)
from .presentation.dependencies.db_dependencies import (
    get_database_session,
    init_database,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings: Settings = app.state.settings
    init_database(settings)
    configure_telemetry(settings)

    if settings._otel_sqlalchemy_instrumentor is not None:
        try:
            settings._otel_sqlalchemy_instrumentor().instrument(
                engine=get_database_session(settings).async_engine.sync_engine
            )
        except Exception:
            logger.exception("Failed to instrument SQLAlchemy with OpenTelemetry")

    yield
    await get_database_session(settings).dispose()


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings)

    app = FastAPI(
        title="Tech Challenge Workshop Service Orders API",
        description=(
            "Backend monolith for customers, vehicles, services, parts and "
            "mechanical workshop service orders."
        ),
        version=settings.APP_VERSION,
        lifespan=lifespan,
    )
    app.state.settings = settings

    if settings.TRUSTED_HOSTS and settings.TRUSTED_HOSTS != ["*"]:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.TRUSTED_HOSTS)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ALLOWED_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app, settings)

    @app.middleware("http")
    async def add_operational_headers_and_logs(request: Request, call_next):
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid4()))
        request_id = request.headers.get("X-Request-ID", correlation_id)
        request.state.correlation_id = correlation_id
        request.state.request_id = request_id
        started_at = perf_counter()
        response = await call_next(request)
        duration_ms = round((perf_counter() - started_at) * 1000, 2)

        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        route_path = request.url.path
        REQUEST_COUNTER.labels(
            method=request.method,
            path=route_path,
            status_code=response.status_code,
        ).inc()
        REQUEST_DURATION.labels(method=request.method, path=route_path).observe(
            duration_ms
        )

        logger.info(
            "Request completed",
            extra={
                "event_name": "http_request_completed",
                "correlation_id": correlation_id,
                "request_id": request_id,
                "method": request.method,
                "path": route_path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "client": request.client.host if request.client else None,
                "service": settings.APP_NAME,
                "env": settings.ENVIRONMENT,
                "version": settings.APP_VERSION,
            },
        )
        return response

    app.include_router(health_router)
    app.include_router(observability_router)
    app.include_router(auth_router)
    app.include_router(public_router)
    app.include_router(service_order_router)
    app.include_router(customer_router)
    app.include_router(vehicle_router)
    app.include_router(catalog_router)
    app.include_router(metrics_router)

    if settings._otel_fastapi_instrumentor is not None:
        try:
            settings._otel_fastapi_instrumentor.instrument_app(app)
        except Exception:
            logger.exception("Failed to instrument FastAPI with OpenTelemetry")

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
