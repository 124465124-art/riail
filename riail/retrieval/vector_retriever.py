"""Retriever that searches the RuleStore and keeps only relevant results.

Built (D1 section 1.4): this is the same logic the target Retrieval function
would run. It decides *which* rules count as relevant; the RuleStore only
stores and ranks them.
"""

from riail.models import RuleChunk, RuleSet
from riail.retrieval.interface import Retriever
from riail.rulestore.interface import RuleStore


class VectorRetriever(Retriever):

    def __init__(self, store: RuleStore, min_score: float = 0.3, max_results: int = 4):
        """
        min_score: results below this are treated as unrelated. If nothing
            passes, the app answers "not covered" (the D1 mitigation for the AI
            inventing a rule). Tuned by the scenario tests.
        max_results: how many rules to pass to the AI. Few enough to keep the
            prompt short, enough to cover situations that combine rules.
        """
        if not 0 <= min_score <= 1:
            raise ValueError("min_score must be between 0 and 1")
        self._store = store
        self._min_score = min_score
        self._max_results = max_results

    def search(self, question: str, rule_set: RuleSet) -> list[RuleChunk]:
        if not question.strip():
            return []
        matches = self._store.search(question, rule_set, limit=self._max_results)
        return [chunk for chunk, score in matches if score >= self._min_score]
