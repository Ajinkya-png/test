import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class ComplianceService:
    """
    Compliance helper for masking PII, recording consent, and maintaining retention policies.
    This file contains simple utility functions rather than a full policy engine.
    """

    @staticmethod
    def mask_phone(phone: str) -> str:
        """Mask a phone number except last 4 digits."""
        if not phone or len(phone) < 4:
            return "****"
        return "*" * (len(phone) - 4) + phone[-4:]

    @staticmethod
    def record_consent(session_id: str, consent_payload: Dict[str, Any]):
        """
        Record consent details. In production this persists to an audit log.
        """
        logger.info(f"Consent recorded for session {session_id}: {consent_payload}")
