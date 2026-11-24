import pytest

from riail.models import Answer, AnswerStatus, RuleSet
from tests.conftest import make_rule


def test_valid_rule_chunk_is_created():
    rule = make_rule()
    assert rule.rule_set is RuleSet.CURRENT
    assert rule.id == "current:4.1"


def test_same_rule_number_has_different_ids_in_each_rule_set():
    assert make_rule(rule_set=RuleSet.CURRENT).id != make_rule(rule_set=RuleSet.TRIAL_2026).id


@pytest.mark.parametrize("field", ["rule_number", "text"])
def test_rule_chunk_rejects_blank_required_fields(field):
    with pytest.raises(ValueError):
        make_rule(**{field: "  "})


def test_rule_chunk_rejects_unknown_rule_set():
    with pytest.raises(ValueError):
        make_rule(rule_set="made_up")


def test_answer_to_dict_matches_ask_contract():
    answer = Answer(status=AnswerStatus.OK, rule_set=RuleSet.CURRENT, text="Explanation.",
                    citations=["4.1"], rules=[make_rule()], answer_id="abc")
    data = answer.to_dict()
    assert set(data) == {"answer_id", "status", "rule_set", "rule_set_label", "answer", "citations", "rules"}
    assert data["status"] == "ok"
    assert data["rule_set"] == "current"
    assert data["citations"] == ["4.1"]
    assert data["rules"][0]["rule_number"] == "4.1"
    assert data["rules"][0]["effective_from"] == "2025-03-10"


def test_not_covered_answer_has_no_text_or_citations():
    answer = Answer(status=AnswerStatus.NOT_COVERED, rule_set=RuleSet.TRIAL_2026)
    assert answer.text == "" and answer.citations == [] and answer.rules == []
