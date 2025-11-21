"""
Compliance utilities:
- DND check (stub; replace with telecom operator data)
- calling window enforcement (TRAI/TCPA)
- consent logging
"""

from datetime import datetime, time
import logging
from typing import Dict, Any
from ..core.database import SessionLocal
from ..models.database import CallSession

logger = logging.getLogger(__name__)

# Allowed call windows (local times). TRAI: 9:00 - 21:00 IST, TCPA US: 8:00 - 21:00 local (example).
TRAI_START = time(9, 0)
TRAI_END = time(21, 0)
TCPA_START = time(8, 0)
TCPA_END = time(21, 0)

def is_within_call_window(local_time: datetime, region: str = "IN") -> bool:
    t = local_time.time()
    if region == "IN":
        return TRAI_START <= t <= TRAI_END
    else:
        return TCPA_START <= t <= TCPA_END

def check_dnd(phone_number: str) -> bool:
    """
    Check DND registry. This is a stub — integrate with telecom DND APIs or a cached list.
    Returns True if DND-listed (i.e., DO NOT CALL).
    """
    # Simple placeholder: treat numbers ending with '000' as DND
    if phone_number.endswith("000"):
        return True
    return False

def record_consent(call_sid: str, consent: Dict[str, Any]):
    """
    Persist consent into call_sessions.metrics or separate table. We'll attach to CallSession.metrics.
    """
    session = SessionLocal()
    try:
        cs = session.query(CallSession).filter(CallSession.call_sid == call_sid).first()
        if not cs:
            logger.warning("Call session not found to record consent")
            return False
        metrics = cs.metrics or {}
        metrics.setdefault("consents", []).append(consent)
        cs.metrics = metrics
        session.commit()
        return True
    except Exception as e:
        logger.exception("Error recording consent")
        session.rollback()
        return False
    finally:
        session.close()
