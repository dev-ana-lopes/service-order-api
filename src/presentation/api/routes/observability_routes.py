from fastapi import APIRouter

from ....infrastructure.observability.metrics import metrics_response

router = APIRouter(tags=["observability"])


@router.get("/metrics")
async def get_application_metrics():
    return metrics_response()
