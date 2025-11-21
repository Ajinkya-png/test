import logging
from typing import List

logger = logging.getLogger(__name__)


class SummarizationService:
    """
    Produces short summaries from conversation transcripts.
    Replace with LLM summarization in production.
    """

    @staticmethod
    def summarize(messages: List[str], max_length: int = 200) -> str:
        """
        Simple heuristic summarizer: join first few messages. For real usage, call LLM.
        """
        if not messages:
            return ""
        joined = " ".join(messages[:5])
        if len(joined) > max_length:
            return joined[:max_length].rsplit(" ", 1)[0] + "..."
        return joined
