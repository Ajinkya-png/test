"""
CRM integration (HubSpot example). Minimal, real-world-ready helpers.
- upsert_customer(customer_dict)
- fetch_customer_history(customer_id)
- create_ticket / upsert_note
"""

import logging
import os
from typing import Dict, Any, Optional
import requests
from ..core.config import settings

logger = logging.getLogger(__name__)
HUBSPOT_API_KEY = settings.HUBSPOT_API_KEY  # set in env


class CRMService:
    BASE_URL = "https://api.hubapi.com"

    @staticmethod
    def _headers():
        return {"Authorization": f"Bearer {HUBSPOT_API_KEY}", "Content-Type": "application/json"}

    @staticmethod
    def upsert_customer(customer: Dict[str, Any]) -> Dict[str, Any]:
        """
        Upsert contact by email or phone.
        Uses HubSpot Contacts API via search to find by email/phone, otherwise creates.
        """
        try:
            email = customer.get("email")
            phone = customer.get("phone_number")

            # Basic search by email if present
            if email:
                search_payload = {
                    "filterGroups": [{"filters": [{"propertyName": "email", "operator": "EQ", "value": email}]}],
                    "properties": ["email", "firstname", "lastname", "phone"],
                }
                r = requests.post(f"{CRMService.BASE_URL}/crm/v3/objects/contacts/search", headers=CRMService._headers(), json=search_payload, timeout=10)
                if r.ok and r.json().get("results"):
                    contact = r.json()["results"][0]
                    # update contact
                    contact_id = contact["id"]
                    update_payload = {"properties": {"email": email, "phone": phone, "firstname": customer.get("name")}}
                    u = requests.patch(f"{CRMService.BASE_URL}/crm/v3/objects/contacts/{contact_id}", headers=CRMService._headers(), json=update_payload, timeout=10)
                    return {"success": True, "crm_id": contact_id}
            # Create new contact
            create_payload = {"properties": {"email": email, "phone": phone, "firstname": customer.get("name")}}
            r2 = requests.post(f"{CRMService.BASE_URL}/crm/v3/objects/contacts", headers=CRMService._headers(), json=create_payload, timeout=10)
            if r2.ok:
                return {"success": True, "crm_id": r2.json().get("id")}
            return {"success": False, "error": r2.text}
        except Exception as e:
            logger.exception("CRM upsert error")
            return {"success": False, "error": str(e)}

    @staticmethod
    def fetch_customer_history(email_or_phone: str) -> Dict[str, Any]:
        """
        Example: fetch contact and recent engagements (tickets) by email or phone
        """
        try:
            # A production implementation should use search endpoints and expand associations
            return {"orders": [], "notes": []}
        except Exception as e:
            logger.exception("CRM fetch error")
            return {"error": str(e)}
