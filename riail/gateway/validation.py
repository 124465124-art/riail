"""Input checks for the API gateway. Bad input is rejected before it reaches the query function."""

from riail.feedback.interface import RATINGS
from riail.models import RuleSet


class ValidationError(ValueError):
    """The request is not acceptable; the message is safe to show the user."""


def validate_ask(payload, max_length: int) -> tuple[str, RuleSet]:
    if not isinstance(payload, dict):
        raise ValidationError("Send the question as JSON.")
    question = payload.get("question")
    if not isinstance(question, str) or not question.strip():
        raise ValidationError("Please type a question.")
    question = " ".join(question.split())  # tidy whitespace and line breaks
    if len(question) > max_length:
        # A length limit also makes long prompt-injection attempts harder (D1 risk register).
        raise ValidationError(f"Please keep your question under {max_length} characters.")
    try:
        rule_set = RuleSet(payload.get("rule_set"))
    except ValueError:
        raise ValidationError("Please choose a rule set.") from None
    return question, rule_set


def validate_feedback(payload) -> tuple[str, str]:
    if not isinstance(payload, dict):
        raise ValidationError("Send the feedback as JSON.")
    answer_id = payload.get("answer_id")
    rating = payload.get("rating")
    if not isinstance(answer_id, str) or not answer_id.strip() or len(answer_id) > 64:
        raise ValidationError("Missing answer id.")
    if rating not in RATINGS:
        raise ValidationError("Rating must be 'up' or 'down'.")
    return answer_id, rating
