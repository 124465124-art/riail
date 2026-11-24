import pytest

from riail.models import RuleSet
from riail.retrieval.vector_retriever import VectorRetriever
from tests.conftest import FakeRuleStore, make_rule


def test_returns_rules_above_the_score_threshold_best_first():
    store = FakeRuleStore([(make_rule("4.1"), 0.8), (make_rule("1.7"), 0.5), (make_rule("2.8"), 0.1)])
    rules = VectorRetriever(store, min_score=0.3).search("too many steps", RuleSet.CURRENT)
    assert [r.rule_number for r in rules] == ["4.1", "1.7"]


def test_nothing_relevant_gives_empty_list_so_app_says_not_covered():
    store = FakeRuleStore([(make_rule("4.1"), 0.1)])
    assert VectorRetriever(store, min_score=0.3).search("offside rule in soccer", RuleSet.CURRENT) == []


def test_blank_question_does_not_search():
    store = FakeRuleStore([(make_rule("4.1"), 0.9)])
    assert VectorRetriever(store).search("   ", RuleSet.CURRENT) == []
    assert store.searches == []


def test_passes_rule_set_and_limit_to_store():
    store = FakeRuleStore([(make_rule("T1", rule_set=RuleSet.TRIAL_2026), 0.9)])
    rules = VectorRetriever(store, max_results=2).search("two handpasses", RuleSet.TRIAL_2026)
    assert store.searches == [("two handpasses", RuleSet.TRIAL_2026, 2)]
    assert rules[0].rule_set is RuleSet.TRIAL_2026


def test_rejects_invalid_threshold():
    with pytest.raises(ValueError):
        VectorRetriever(FakeRuleStore(), min_score=1.5)


# With the real rule files (keyword vectors, so no model download)

def test_known_question_returns_expected_rule(loaded_store):
    rules = VectorRetriever(loaded_store, min_score=0.1).search(
        "square ball: attacker inside the small rectangle before the ball", RuleSet.CURRENT)
    assert "4.10" in [r.rule_number for r in rules]


def test_trial_rules_are_left_out_when_current_rules_chosen(loaded_store):
    rules = VectorRetriever(loaded_store, min_score=0.0, max_results=10).search(
        "consecutive handpasses two in a row", RuleSet.CURRENT)
    assert all(r.rule_set is RuleSet.CURRENT for r in rules)
    assert "T1" not in [r.rule_number for r in rules]


def test_trial_rule_set_finds_trial_version_of_steps_rule(loaded_store):
    rules = VectorRetriever(loaded_store, min_score=0.1).search(
        "how many steps can a player carry the ball", RuleSet.TRIAL_2026)
    steps_rule = next(r for r in rules if r.rule_number == "1.7")
    assert "six steps" in steps_rule.text
