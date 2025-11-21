from fastapi import APIRouter, Response
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/monitoring/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "ok"}


@router.get("/metrics")
async def metrics():
    """
    Return Prometheus-style metrics text (placeholder).
    In production this would integrate with prometheus_client exposition.
    """
    content = "# HELP food_delivery_calls_total Total number of calls\nfood_delivery_calls_total 1234\n"
    return Response(content=content, media_type="text/plain")

@router.get("/health")
async def health_check():
    return {"status": "ok", "message": "Server is healthy"}