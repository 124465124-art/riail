"""Data shared between Riail's components.

Every component passes these objects to each other, so this file is the
common "language" of the system. It holds data only: no searching, no AI calls.
"""

from dataclasses import dataclass, field
from datetime import date
from enum import Enum


class RuleSet(str, Enum):
    """Which rulebook a rule belongs to.

    Tagging every rule with its rule set is the mitigation for the D1 risk
    "a trial rule is shown as a current rule, or the other way round".
    """

    CURRENT = "current"        # Official Guide rules used in club games
    TRIAL_2026 = "trial_2026"  # experimental rules in the college league

    @property
    def label(self) -> str:
        """Name shown to users."""
        return {
            RuleSet.CURRENT: "Club game: current rules",
            RuleSet.TRIAL_2026: "College game: 2026 trial rules",
        }[self]


class AnswerStatus(str, Enum):
    """How an answer was produced, so the front end knows what to show."""

    OK = "ok"                    # AI explanation with citations
    NOT_COVERED = "not_covered"  # no relevant rule found, so the app does not guess
    FALLBACK = "fallback"        # AI failed, so only the matching rules are shown


@dataclass(frozen=True)
class RuleChunk:
    """One rule (or a small group of related rules) from the rulebook."""

    rule_number: str        # e.g. "4.1", or "T1" for a trial-only rule
    rule_set: RuleSet
    text: str               # rule wording (paraphrased in this prototype, see README)
    effective_from: date    # when this version of the rule came into force
    source: str             # where the rule comes from
    title: str = ""         # short heading, e.g. "Overcarrying"

    def __post_init__(self):
        if not self.rule_number.strip():
            raise ValueError("A rule chunk must have a rule number")
        if not self.text.strip():
            raise ValueError("A rule chunk must have rule text")
        if not isinstance(self.rule_set, RuleSet):
            raise ValueError(f"Unknown rule set: {self.rule_set!r}")

    @property
    def id(self) -> str:
        """Unique key in the rule store: the same number can exist in both rule sets."""
        return f"{self.rule_set.value}:{self.rule_number}"


@dataclass(frozen=True)
class Answer:
    """What the app sends back for one question."""

    status: AnswerStatus
    rule_set: RuleSet
    text: str = ""                                        # explanation (empty unless status is OK)
    citations: list[str] = field(default_factory=list)    # rule numbers the explanation relies on
    rules: list[RuleChunk] = field(default_factory=list)  # the rule text shown to the user
    answer_id: str = ""                                   # lets feedback refer to an answer without storing the question

    def to_dict(self) -> dict:
        """Shape of the JSON returned by POST /ask (the HTTP contract kept from D1)."""
        return {
            "answer_id": self.answer_id,
            "status": self.status.value,
            "rule_set": self.rule_set.value,
            "rule_set_label": self.rule_set.label,
            "answer": self.text,
            "citations": self.citations,
            "rules": [
                {
                    "rule_number": r.rule_number,
                    "title": r.title,
                    "text": r.text,
                    "source": r.source,
                    "effective_from": r.effective_from.isoformat(),
                }
                for r in self.rules
            ],
        }
