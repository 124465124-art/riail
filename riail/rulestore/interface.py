"""RuleStore interface: holds the rules and lets the app search them.

The prototype uses a local Chroma file (Simplified); the target would use a
managed vector database. Both must provide these methods, so nothing else
changes when the store is swapped.
"""

from abc import ABC, abstractmethod

from riail.models import RuleChunk, RuleSet


class RuleStore(ABC):

    @abstractmethod
    def add(self, chunks: list[RuleChunk]) -> None:
        """Save rule chunks. A chunk with the same id as a stored one replaces it.

        Only the ingestion script calls this.
        """

    @abstractmethod
    def clear(self) -> None:
        """Remove every rule, so a reload does not leave old rules behind."""

    @abstractmethod
    def search(self, query: str, rule_set: RuleSet, limit: int) -> list[tuple[RuleChunk, float]]:
        """Return up to `limit` rules from `rule_set` that best match `query`, best first.

        Each result comes with a relevance score from 0 (unrelated) to 1
        (very close). Rules from any other rule set must never be returned.
        """

    @abstractmethod
    def count(self, rule_set: RuleSet | None = None) -> int:
        """How many rules are stored, optionally for one rule set only."""
