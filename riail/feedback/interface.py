"""FeedbackLog interface: records answer ratings and AI errors.

No personal data is stored: never the question text, only an answer id,
the rating, the rule set and the citations (D1 privacy risk).
"""

from abc import ABC, abstractmethod

from riail.models import Answer

RATINGS = ("up", "down")


class FeedbackLog(ABC):

    @abstractmethod
    def record_answer(self, answer: Answer) -> None:
        """Note that an answer was given (status, rule set, citations; no question text)."""

    @abstractmethod
    def record_rating(self, answer_id: str, rating: str) -> None:
        """Save a like ("up") or dislike ("down") for an answer. Raises ValueError for anything else."""

    @abstractmethod
    def record_error(self, kind: str, detail: str) -> None:
        """Save an AI failure, so outages and bad replies can be reviewed."""
