"""Shared test helpers. Tests never call the real AI or download the embedding model."""

from datetime import date

from riail.models import RuleChunk, RuleSet


def make_rule(rule_number="4.1", rule_set=RuleSet.CURRENT, text="Example rule text.",
              title="Example", effective_from=date(2025, 3, 10), source="Test source"):
    return RuleChunk(rule_number=rule_number, rule_set=rule_set, text=text, title=title,
                     effective_from=effective_from, source=source)
