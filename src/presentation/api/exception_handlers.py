from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from ...domain.errors import DomainError
from ...infrastructure.config.settings import Settings
from ...infrastructure.observability.metrics import SERVICE_ORDER_FAILURES

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI, settings: Settings) -> None:
    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        logger.warning(
            "Request validation failed",
            extra={
                "event_name": "request_validation_failed",
                "correlation_id": getattr(request.state, "correlation_id", None),
                "request_id": getattr(request.state, "request_id", None),
                "method": request.method,
                "path": request.url.path,
                "errors": exc.errors(),
            },
        )
        return JSONResponse(
            status_code=422,
            content={
                "detail": "Validation failed",
                "errors": exc.errors(),
            },
        )

    @app.exception_handler(DomainError)
    async def handle_domain_error(
        request: Request,
        exc: DomainError,
    ) -> JSONResponse:
        logger.warning(
            "Domain error",
            extra={
                "event_name": "domain_error",
                "correlation_id": getattr(request.state, "correlation_id", None),
                "request_id": getattr(request.state, "request_id", None),
                "method": request.method,
                "path": request.url.path,
                "error_type": exc.__class__.__name__,
            },
        )
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(Exception)
    async def handle_unexpected_error(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        if request.url.path.startswith("/service-orders"):
            SERVICE_ORDER_FAILURES.labels(stage="unhandled_exception").inc()
        logger.exception(
            "Unhandled application error",
            extra={
                "event_name": "service_order_processing_failed"
                if request.url.path.startswith("/service-orders")
                else "unhandled_application_error",
                "correlation_id": getattr(request.state, "correlation_id", None),
                "request_id": getattr(request.state, "request_id", None),
                "method": request.method,
                "path": request.url.path,
                "error_type": exc.__class__.__name__,
            },
        )
        detail = (
            str(exc)
            if settings.ENVIRONMENT in {"development", "test"}
            else "Internal server error"
        )
        return JSONResponse(status_code=500, content={"detail": detail})
