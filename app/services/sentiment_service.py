import logging
from typing import Dict

logger = logging.getLogger(__name__)


class SentimentService:
    """
    Simple sentiment scoring helper. In production, use a pre-trained model or API.
    """

    @staticmethod
    def score_text(text: str) -> Dict[str, float]:
        """
        Return a mock sentiment score between -1 (negative) and 1 (positive).
        """
        if not text:
            return {"score": 0.0}
        lower = text.lower()
        if any(w in lower for w in ["angry", "frustrated", "terrible", "not happy", "refund"]):
            return {"score": -0.8}
        if any(w in lower for w in ["thank", "great", "good", "awesome", "nice"]):
            return {"score": 0.8}
        return {"score": 0.0}
