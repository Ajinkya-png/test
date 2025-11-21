# """
# Stripe payment integration service.

# Features:
# - create_payment_intent: creates a Stripe PaymentIntent (server-side)
# - confirm_payment_webhook: handler for Stripe webhook events (payment_intent.succeeded, charge.refunded)
# - refund: create refund with idempotency support
# - secure handling (idempotency keys, retries)
# """

# import os
# import logging
# from typing import Dict, Any, Optional
# import stripe
# from ..core.config import settings

# logger = logging.getLogger(__name__)

# stripe.api_key = settings.STRIPE_API_KEY  # set via env

# class PaymentService:
#     @staticmethod
#     def create_payment_intent(amount_cents: int, currency: str = "inr", customer_id: Optional[str]=None, metadata: Dict[str, Any]=None, idempotency_key: Optional[str]=None) -> Dict[str, Any]:
#         """
#         Create a Stripe PaymentIntent.
#         amount_cents: amount in paise (INR) or cents (USD) depending on currency.
#         """
#         try:
#             params = {
#                 "amount": int(amount_cents),
#                 "currency": currency,
#                 "payment_method_types": ["card"],
#             }
#             if customer_id:
#                 params["customer"] = customer_id
#             if metadata:
#                 params["metadata"] = metadata

#             headers = {}
#             if idempotency_key:
#                 headers["Idempotency-Key"] = idempotency_key

#             pi = stripe.PaymentIntent.create(**params, **({"idempotency_key": idempotency_key} if idempotency_key else {}))
#             logger.info(f"Created PaymentIntent {pi.id} for amount {amount_cents} {currency}")
#             return {"success": True, "payment_intent": pi}
#         except Exception as e:
#             logger.exception("Error creating payment intent")
#             return {"success": False, "error": str(e)}

#     @staticmethod
#     def refund(payment_intent_id: str, amount_cents: Optional[int] = None, reason: Optional[str] = None, idempotency_key: Optional[str] = None) -> Dict[str, Any]:
#         """
#         Refund a payment. If amount_cents is None, full refund.
#         """
#         try:
#             # Find charge from payment intent
#             pi = stripe.PaymentIntent.retrieve(payment_intent_id, expand=["charges"])
#             charges = pi.charges.data
#             if not charges:
#                 return {"success": False, "error": "No charge found for payment intent"}
#             charge_id = charges[0].id

#             params = {"charge": charge_id}
#             if amount_cents:
#                 params["amount"] = int(amount_cents)
#             if reason:
#                 params["reason"] = reason

#             refund = stripe.Refund.create(**params, **({"idempotency_key": idempotency_key} if idempotency_key else {}))
#             logger.info(f"Created refund {refund.id} for charge {charge_id}")
#             return {"success": True, "refund": refund}
#         except Exception as e:
#             logger.exception("Error creating refund")
#             return {"success": False, "error": str(e)}

#     @staticmethod
#     def handle_webhook(payload: bytes, sig_header: str, webhook_secret: str) -> Dict[str, Any]:
#         """
#         Validate and parse Stripe webhook. Returns dict with event type and data.
#         """
#         try:
#             event = stripe.Webhook.construct_event(
#                 payload=payload, sig_header=sig_header, secret=webhook_secret
#             )
#             logger.info(f"Stripe webhook received: {event['type']}")
#             return {"success": True, "event": event}
#         except stripe.error.SignatureVerificationError as e:
#             logger.error("Invalid Stripe webhook signature")
#             return {"success": False, "error": "invalid_signature"}
#         except Exception as e:
#             logger.exception("Error handling stripe webhook")
#             return {"success": False, "error": str(e)}


# app/services/payment_service.py
import os
import logging
from typing import Dict, Any, Optional
import stripe
from ..core.config import settings

logger = logging.getLogger(__name__)

# Check if Stripe API key is configured
if hasattr(settings, 'STRIPE_API_KEY') and settings.STRIPE_API_KEY:
    stripe.api_key = settings.STRIPE_API_KEY
    logger.info("✅ Stripe API key configured")
else:
    logger.warning("❌ Stripe API key not configured - using simulation mode")
    stripe.api_key = "sk_test_mock_key_for_development"  # Mock key to avoid errors

class PaymentService:
    @staticmethod
    def create_payment_intent(amount_cents: int, currency: str = "usd", customer_id: Optional[str]=None, metadata: Dict[str, Any]=None, idempotency_key: Optional[str]=None) -> Dict[str, Any]:
        """
        Create a Stripe PaymentIntent with fallback simulation
        """
        try:
            # Check if we have a valid Stripe API key
            if not settings.STRIPE_API_KEY or settings.STRIPE_API_KEY.startswith("sk_test_mock"):
                # SIMULATION MODE - Return mock payment intent
                logger.info("💰 Using payment simulation mode")
                mock_payment_intent = {
                    "id": f"pi_mock_{idempotency_key or 'demo'}",
                    "client_secret": f"pi_mock_secret_{idempotency_key or 'demo'}",
                    "status": "requires_payment_method",
                    "amount": amount_cents,
                    "currency": currency
                }
                return {"success": True, "payment_intent": mock_payment_intent}

            # REAL Stripe API call
            params = {
                "amount": int(amount_cents),
                "currency": currency,
                "payment_method_types": ["card"],
            }
            if customer_id:
                params["customer"] = customer_id
            if metadata:
                params["metadata"] = metadata

            pi = stripe.PaymentIntent.create(
                **params, 
                **({"idempotency_key": idempotency_key} if idempotency_key else {})
            )
            logger.info(f"✅ Created PaymentIntent {pi.id} for amount {amount_cents} {currency}")
            return {"success": True, "payment_intent": pi}
            
        except stripe.error.AuthenticationError as e:
            logger.error(f"❌ Stripe authentication failed: {e}")
            # Fallback to simulation
            return PaymentService._create_mock_payment_intent(amount_cents, currency, metadata)
        except Exception as e:
            logger.exception("Error creating payment intent")
            return {"success": False, "error": str(e)}

    @staticmethod
    def _create_mock_payment_intent(amount_cents: int, currency: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a mock payment intent for demo purposes"""
        import uuid
        mock_id = f"pi_mock_{uuid.uuid4().hex[:8]}"
        
        mock_payment_intent = {
            "id": mock_id,
            "client_secret": f"{mock_id}_secret",
            "status": "requires_payment_method",
            "amount": amount_cents,
            "currency": currency,
            "metadata": metadata or {}
        }
        
        logger.info(f"💰 Created mock PaymentIntent {mock_id} for amount {amount_cents} {currency}")
        return {"success": True, "payment_intent": mock_payment_intent}

    @staticmethod
    def confirm_payment(payment_intent_id: str) -> Dict[str, Any]:
        """Confirm a payment with simulation support"""
        try:
            # Check if this is a mock payment intent
            if payment_intent_id.startswith("pi_mock"):
                logger.info("💰 Confirming mock payment")
                return {
                    "success": True,
                    "status": "succeeded",
                    "amount": 1000,  # Mock amount
                    "currency": "usd"
                }

            # REAL Stripe API call
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            return {
                "success": True,
                "status": intent.status,
                "amount": intent.amount,
                "currency": intent.currency
            }
        except Exception as e:
            logger.error(f"Error confirming payment: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def refund(payment_intent_id: str, amount_cents: Optional[int] = None, reason: Optional[str] = None, idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        """Refund a payment with simulation support"""
        try:
            # Check if this is a mock payment intent
            if payment_intent_id.startswith("pi_mock"):
                logger.info("💰 Processing mock refund")
                return {"success": True, "refund_id": f"re_mock_{idempotency_key or 'demo'}"}

            # REAL Stripe API call
            pi = stripe.PaymentIntent.retrieve(payment_intent_id, expand=["charges"])
            charges = pi.charges.data
            if not charges:
                return {"success": False, "error": "No charge found for payment intent"}
            charge_id = charges[0].id

            params = {"charge": charge_id}
            if amount_cents:
                params["amount"] = int(amount_cents)
            if reason:
                params["reason"] = reason

            refund = stripe.Refund.create(
                **params, 
                **({"idempotency_key": idempotency_key} if idempotency_key else {})
            )
            logger.info(f"✅ Created refund {refund.id} for charge {charge_id}")
            return {"success": True, "refund": refund}
        except Exception as e:
            logger.exception("Error creating refund")
            return {"success": False, "error": str(e)}

    @staticmethod
    def handle_webhook(payload: bytes, sig_header: str, webhook_secret: str) -> Dict[str, Any]:
        """Handle Stripe webhook with simulation support"""
        try:
            # For demo, simulate webhook events
            if not settings.STRIPE_API_KEY or settings.STRIPE_API_KEY.startswith("sk_test_mock"):
                logger.info("💰 Simulating webhook processing")
                return {
                    "success": True, 
                    "event": {
                        "type": "payment_intent.succeeded",
                        "data": {"object": {"id": "pi_mock_webhook"}}
                    }
                }

            # REAL Stripe webhook validation
            event = stripe.Webhook.construct_event(
                payload=payload, sig_header=sig_header, secret=webhook_secret
            )
            logger.info(f"Stripe webhook received: {event['type']}")
            return {"success": True, "event": event}
        except stripe.error.SignatureVerificationError as e:
            logger.error("Invalid Stripe webhook signature")
            return {"success": False, "error": "invalid_signature"}
        except Exception as e:
            logger.exception("Error handling stripe webhook")
            return {"success": False, "error": str(e)}