from fastapi import APIRouter, HTTPException
import logging
from typing import Dict, Any

from ..agents import CustomerOrderAgent

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/agents/customer-order/process")
async def process_customer_message(payload: Dict[str, Any]):
    """
    Simple API endpoint to send a text message to the customer_order_agent.
    Payload:
    {
        "message": "I want pizza",
        "session_data": {...}
    }
    """
    try:
        message = payload.get("message")
        session_data = payload.get("session_data", {})

        if not message:
            raise HTTPException(status_code=400, detail="Missing 'message'")

        agent = CustomerOrderAgent()
        result = await agent.process_message(message, session_data)
        return {"success": True, "response": result}
    except Exception as e:
        logger.error(f"Error in agents router: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def agents_root():
    return {"message": "Agents API is working."}
