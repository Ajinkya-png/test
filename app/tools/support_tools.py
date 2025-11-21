"""
Support Tools Module
====================

Provides utilities for the Support Agent to:
- Create and manage support tickets
- Process refunds via PaymentService
- Log customer complaints in CRM
- Escalate unresolved issues
- Notify users about resolutions via Twilio

All functions return structured JSON for consistent AI tool calling.
"""

import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from ..services.payment_service import PaymentService
from ..services.crm_service import CRMService
from ..services.twilio_service import TwilioService
from ..core.database import SessionLocal
from ..models.database import Order, SupportTicket

logger = logging.getLogger(__name__)

# ============================================================
# SUPPORT TICKET CREATION
# ============================================================

def create_support_ticket(order_id: str, issue: str, severity: str = "medium") -> Dict[str, Any]:
    """
    Create a new support ticket in the system database.

    Args:
        order_id: ID of the related order
        issue: description of the problem
        severity: low / medium / high (default=medium)

    Returns:
        dict: ticket details
    """
    db = SessionLocal()
    try:
        ticket_id = f"TKT-{uuid.uuid4().hex[:8]}"
        ticket = SupportTicket(
            ticket_id=ticket_id,
            order_id=order_id,
            issue=issue,
            severity=severity,
            status="open",
            created_at=datetime.utcnow()
        )
        db.add(ticket)
        db.commit()

        logger.info(f"Created support ticket {ticket_id} for order {order_id}")

        return {
            "success": True,
            "id": ticket_id,
            "order_id": order_id,
            "status": "open",
            "message": f"Support ticket created for issue: {issue}",
        }
    except Exception as e:
        db.rollback()
        logger.exception("Failed to create support ticket")
        return {"success": False, "error": str(e)}
    finally:
        db.close()

# ============================================================
# ISSUE ESCALATION
# ============================================================

def escalate_ticket(ticket_id: str, reason: Optional[str] = None) -> Dict[str, Any]:
    """
    Escalate a support ticket for human review or priority handling.

    Args:
        ticket_id: ID of the support ticket
        reason: escalation reason

    Returns:
        dict: escalation confirmation
    """
    db = SessionLocal()
    try:
        ticket = db.query(SupportTicket).filter_by(ticket_id=ticket_id).first()
        if not ticket:
            return {"success": False, "error": "Ticket not found"}

        ticket.status = "escalated"
        ticket.updated_at = datetime.utcnow()
        db.commit()

        logger.warning(f"Ticket {ticket_id} escalated: {reason or 'No reason provided'}")

        # Sync escalation to CRM
        CRMService.upsert_customer({"email": "support@voiceai.io", "name": "Support Escalation"})
        return {"success": True, "message": f"Ticket {ticket_id} escalated for review."}
    except Exception as e:
        db.rollback()
        logger.exception("Escalation failed")
        return {"success": False, "error": str(e)}
    finally:
        db.close()

# ============================================================
# REFUND PROCESSING
# ============================================================

def process_refund(order_id: str, reason: str, partial: bool = False, amount_cents: Optional[int] = None) -> Dict[str, Any]:
    """
    Trigger a refund for a given order via Stripe.

    Args:
        order_id: ID of the order
        reason: reason for refund
        partial: whether to refund partially
        amount_cents: optional partial amount

    Returns:
        dict: refund status
    """
    db = SessionLocal()
    try:
        order = db.query(Order).filter_by(order_id=order_id).first()
        if not order:
            return {"success": False, "error": "Order not found"}

        payment_intent = order.payment_intent_id
        if not payment_intent:
            return {"success": False, "error": "No payment record found"}

        logger.info(f"Initiating refund for order {order_id}")
        refund_res = PaymentService.refund(
            payment_intent_id=payment_intent,
            amount_cents=amount_cents if partial else None,
            reason=reason,
        )

        if not refund_res.get("success"):
            raise Exception(refund_res.get("error"))

        # Mark order refunded in DB
        order.status = "refunded"
        order.updated_at = datetime.utcnow()
        db.commit()

        return {
            "success": True,
            "order_id": order_id,
            "refund_id": refund_res["refund"].id if refund_res.get("refund") else None,
            "status": "refunded",
        }
    except Exception as e:
        db.rollback()
        logger.exception("Refund failed")
        return {"success": False, "error": str(e)}
    finally:
        db.close()

# ============================================================
# CUSTOMER NOTIFICATION
# ============================================================

def notify_customer(phone_number: str, message: str) -> Dict[str, Any]:
    """
    Send SMS notification to a customer via Twilio.

    Args:
        phone_number: target number
        message: SMS body text
    """
    try:
        TwilioService.send_sms(to=phone_number, message=message)
        logger.info(f"Sent SMS to {phone_number}: {message}")
        return {"success": True, "message": "Notification sent."}
    except Exception as e:
        logger.exception("Failed to send SMS notification")
        return {"success": False, "error": str(e)}

# ============================================================
# COMPLAINT LOGGING
# ============================================================

def log_complaint_to_crm(customer_email: str, complaint_text: str) -> Dict[str, Any]:
    """
    Create a support note or complaint in the CRM (HubSpot example).

    Args:
        customer_email: customer's email address
        complaint_text: text of the complaint
    """
    try:
        res = CRMService.upsert_customer({"email": customer_email})
        if not res.get("success"):
            return {"success": False, "error": "CRM sync failed"}
        crm_id = res["crm_id"]
        logger.info(f"Complaint logged for {customer_email}: {complaint_text}")
        return {"success": True, "crm_id": crm_id, "message": "Complaint recorded in CRM."}
    except Exception as e:
        logger.exception("Failed to log complaint")
        return {"success": False, "error": str(e)}

# ============================================================
# TICKET RESOLUTION
# ============================================================

def resolve_ticket(ticket_id: str, resolution_note: str) -> Dict[str, Any]:
    """
    Resolve a support ticket and update CRM / notify customer.

    Args:
        ticket_id: ID of the ticket
        resolution_note: final resolution text
    """
    db = SessionLocal()
    try:
        ticket = db.query(SupportTicket).filter_by(ticket_id=ticket_id).first()
        if not ticket:
            return {"success": False, "error": "Ticket not found"}

        ticket.status = "resolved"
        ticket.resolution_note = resolution_note
        ticket.updated_at = datetime.utcnow()
        db.commit()

        # Log in CRM
        CRMService.upsert_customer({"email": "support@voiceai.io"})
        logger.info(f"Ticket {ticket_id} resolved: {resolution_note}")
        return {"success": True, "message": f"Ticket {ticket_id} marked as resolved."}
    except Exception as e:
        db.rollback()
        logger.exception("Ticket resolution failed")
        return {"success": False, "error": str(e)}
    finally:
        db.close()

# ============================================================
# END OF FILE
# ============================================================
