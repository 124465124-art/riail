"""Retriever interface: finds the rules relevant to a question.

Preserved between prototype and target (D1, section 1.4).
"""

from abc import ABC, abstractmethod

from riail.models import RuleChunk, RuleSet


class Retriever(ABC):

    @abstractmethod
    def search(self, question: str, rule_set: RuleSet) -> list[RuleChunk]:
        """Return the rules from `rule_set` relevant to `question`, best first.

        An empty list means no relevant rule was found, and the app will
        answer "not covered" instead of guessing.
        """
