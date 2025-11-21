from fastapi import APIRouter, Request, HTTPException, Header
from typing import Dict
from ..services.payment_service import PaymentService
from ..core.config import settings
import logging

router = APIRouter(prefix="/payments")
logger = logging.getLogger(__name__)

@router.post("/create-intent")
async def create_intent(payload: Dict):
    """
    Create a payment intent.
    payload: { "amount_cents": 10000, "currency": "inr", "customer_id": "...", "idempotency_key": "..." }
    """
    amount = payload.get("amount_cents")
    currency = payload.get("currency", "inr")
    if not amount:
        raise HTTPException(status_code=400, detail="Missing amount_cents")

    result = PaymentService.create_payment_intent(
        amount_cents=amount, currency=currency, customer_id=payload.get("customer_id"), metadata=payload.get("metadata"), idempotency_key=payload.get("idempotency_key")
    )
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    return {"success": True, "payment_intent": result["payment_intent"].id}

@router.post("/webhook")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None)):
    """
    Stripe webhook endpoint. Configure your Stripe dashboard to POST here.
    """
    body = await request.body()
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET
    res = PaymentService.handle_webhook(body, stripe_signature, webhook_secret)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    event = res["event"]
    # handle types: payment_intent.succeeded, charge.refunded, payment_intent.payment_failed, etc.
    # Example:
    if event["type"] == "payment_intent.succeeded":
        pi = event["data"]["object"]
        logger.info(f"PaymentIntent succeeded: {pi['id']}")
        # TODO: update order/payment status in DB
    return {"ok": True}
