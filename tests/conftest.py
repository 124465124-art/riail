"""Shared test helpers. Tests never call the real AI or download the embedding model."""

from datetime import date
from pathlib import Path

import pytest

from riail.embedding.keyword import KeywordEmbedder
from riail.ingestion.load_rules import load
from riail.models import RuleChunk, RuleSet
from riail.rulestore.chroma_store import ChromaRuleStore
from riail.rulestore.interface import RuleStore

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "rules"


def make_rule(rule_number="4.1", rule_set=RuleSet.CURRENT, text="Example rule text.",
              title="Example", effective_from=date(2025, 3, 10), source="Test source"):
    return RuleChunk(rule_number=rule_number, rule_set=rule_set, text=text, title=title,
                     effective_from=effective_from, source=source)


class FakeRuleStore(RuleStore):
    """In-memory store returning fixed scores, so the Retriever can be tested on its own."""

    def __init__(self, scored: list[tuple[RuleChunk, float]] = ()):
        self.scored = list(scored)
        self.searches = []

    def add(self, chunks):
        self.scored.extend((c, 1.0) for c in chunks)

    def clear(self):
        self.scored = []

    def search(self, query, rule_set, limit):
        self.searches.append((query, rule_set, limit))
        hits = [(c, s) for c, s in self.scored if c.rule_set == rule_set]
        return sorted(hits, key=lambda h: h[1], reverse=True)[:limit]

    def count(self, rule_set=None):
        return len([c for c, _ in self.scored if rule_set is None or c.rule_set == rule_set])


@pytest.fixture
def loaded_store():
    """A real Chroma store (in memory) loaded with the real rule files, using keyword vectors."""
    store = ChromaRuleStore(embedder=KeywordEmbedder())
    load(store, DATA_DIR)
    return store
