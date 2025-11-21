import logging
from typing import Dict, Any
from ..core.database import SessionLocal

logger = logging.getLogger(__name__)


class AnalyticsService:
    """
    Lightweight analytics service for recording events and computing simple summaries.
    In production, this would write to a time-series DB or analytics warehouse.
    """

    @staticmethod
    def record_event(event_name: str, payload: Dict[str, Any]):
        """
        Record an analytics event. For now this logs to the app logger.
        """
        logger.info(f"Analytics event: {event_name} | payload: {payload}")

    @staticmethod
    def get_summary() -> Dict[str, Any]:
        """
        Return a mocked analytics summary. Replace with DB queries as needed.
        """
        return {
            "total_calls": 1234,
            "average_call_length_seconds": 180,
            "orders_placed": 456,
            "refunds_processed": 12
        }
