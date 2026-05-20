from __future__ import annotations

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.responses import Response

REQUEST_COUNTER = Counter(
    "http_requests_total",
    "Total HTTP requests processed by the API.",
    ["method", "path", "status_code"],
)
REQUEST_DURATION = Histogram(
    "http_request_duration_ms",
    "HTTP request duration in milliseconds.",
    ["method", "path"],
    buckets=(5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000),
)
SERVICE_ORDERS_CREATED = Counter(
    "service_orders_created_total",
    "Number of service orders created.",
)
SERVICE_ORDER_FAILURES = Counter(
    "service_order_processing_failures_total",
    "Number of service order processing failures.",
    ["stage"],
)
SERVICE_ORDER_STATUS = Counter(
    "service_order_status_total",
    "Number of service order events by status.",
    ["status"],
)


def metrics_response() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
