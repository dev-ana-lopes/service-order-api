from .auth_routes import router as auth_router
from .catalog_routes import router as catalog_router
from .customer_routes import router as customer_router
from .health_routes import router as health_router
from .metrics_routes import router as metrics_router
from .observability_routes import router as observability_router
from .public_routes import router as public_router
from .service_order_routes import router as service_order_router
from .vehicle_routes import router as vehicle_router

__all__ = [
    "auth_router",
    "catalog_router",
    "customer_router",
    "health_router",
    "metrics_router",
    "observability_router",
    "public_router",
    "service_order_router",
    "vehicle_router",
]
