from fastapi import APIRouter
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/analytics/summary")
async def analytics_summary():
    """
    Placeholder endpoint returning mocked analytics summary.
    In production this would query analytics DB or time-series.
    """
    return {
        "total_calls": 1234,
        "average_call_length_seconds": 180,
        "orders_placed": 456,
        "refunds_processed": 12
    }

@router.get("/")
async def analytics_root():
    return {"message": "Analytics API is working."}