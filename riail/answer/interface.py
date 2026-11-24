"""Answerer interface: the AI component.

Takes a question and the retrieved rules and returns a plain-language
explanation that cites them. The real version calls an LLM; the mock
version returns fixed replies for tests. Preserved between prototype and
target (D1, section 1.4).
"""

from abc import ABC, abstractmethod

from riail.models import Answer, RuleChunk


class AnswererError(Exception):
    """Raised when the AI cannot give a usable answer.

    Covers a timeout, the service being down, the free-tier limit being
    reached, or a reply that fails the citation checks. The query function
    catches this and shows the matching rules instead (the D1 fallback).
    """


class Answerer(ABC):

    @abstractmethod
    def answer(self, question: str, rules: list[RuleChunk]) -> Answer:
        """Explain how `rules` apply to `question`.

        Returns an Answer with status OK (an explanation whose citations all
        come from `rules`) or NOT_COVERED (the rules do not answer the
        question). Raises AnswererError if a usable answer cannot be
        produced. `rules` is never empty in normal use: the query function
        handles "not covered" before calling this.
        """
