from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/orders/calculate")
async def calculate_order(payload: Dict[str, Any]):
    """
    Accepts session_data with order_items to calculate totals (delegates to tools in production).
    """
    try:
        session_data = payload.get("session_data", {})
        # Call the customer_tools.calculate_total in production
        from ..tools.customer_tools import calculate_total
        result = await calculate_total(session_data)
        return {"success": True, "totals": result}
    except Exception as e:
        logger.error(f"Error calculating order: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get("/")
async def orders_root():
    return {"message": "Orders API is working."}

