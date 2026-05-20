from __future__ import annotations

import logging

from ..config.settings import Settings

logger = logging.getLogger(__name__)


def configure_telemetry(settings: Settings) -> None:
    if not settings.OTEL_ENABLED:
        return

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except Exception:
        logger.exception("OpenTelemetry dependencies could not be loaded")
        return

    resource = Resource.create(
        {
            "service.name": settings.OTEL_SERVICE_NAME,
            "deployment.environment": settings.ENVIRONMENT,
            "service.version": settings.APP_VERSION,
        }
    )
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)

    if settings.OTEL_EXPORTER_OTLP_ENDPOINT:
        exporter = OTLPSpanExporter(endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT)
        provider.add_span_processor(BatchSpanProcessor(exporter))

    settings._otel_fastapi_instrumentor = FastAPIInstrumentor
    settings._otel_sqlalchemy_instrumentor = SQLAlchemyInstrumentor
