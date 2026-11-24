import json

import pytest

from riail.ingestion.load_rules import RuleFileError, build_rule_sets, load, read_rule_file
from riail.models import RuleSet
from tests.conftest import DATA_DIR, FakeRuleStore


def write(path, data):
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


BASE = {"rule_set": "current", "source": "S", "effective_from": "2025-03-10",
        "rules": [{"rule_number": "1.7", "title": "Steps", "text": "Four steps."},
                  {"rule_number": "4.1", "title": "Overcarry", "text": "More than four steps."}]}
TRIAL = {"rule_set": "trial_2026", "base": "current", "source": "T", "effective_from": "2026-10-01",
         "rules": [{"rule_number": "1.7", "title": "Steps", "text": "Six steps."},
                   {"rule_number": "T1", "title": "Handpasses", "text": "No two in a row."}]}


# The real rule files

def test_every_real_rule_has_a_rule_number_rule_set_and_text():
    chunks = build_rule_sets(DATA_DIR)
    assert chunks
    for c in chunks:
        assert c.rule_number.strip() and c.text.strip()
        assert isinstance(c.rule_set, RuleSet)


def test_real_files_fill_both_rule_sets_with_unique_ids():
    chunks = build_rule_sets(DATA_DIR)
    assert {c.rule_set for c in chunks} == set(RuleSet)
    ids = [c.id for c in chunks]
    assert len(ids) == len(set(ids))


def test_real_trial_set_replaces_steps_rule_and_keeps_unchanged_rules():
    trial = {c.rule_number: c for c in build_rule_sets(DATA_DIR) if c.rule_set is RuleSet.TRIAL_2026}
    assert "six steps" in trial["1.7"].text
    assert "T1" in trial
    assert "2.8" in trial and "TRIAL RULE" not in trial["2.8"].text  # copied from the current rules


# Overlay logic and file checks

def test_trial_overlay_replaces_and_adds(tmp_path):
    write(tmp_path / "current.json", BASE)
    write(tmp_path / "trial.json", TRIAL)
    trial = {c.rule_number: c.text for c in build_rule_sets(tmp_path) if c.rule_set is RuleSet.TRIAL_2026}
    assert trial == {"1.7": "Six steps.", "T1": "No two in a row.", "4.1": "More than four steps."}


def test_rule_without_rule_number_is_rejected(tmp_path):
    bad = dict(BASE, rules=[{"title": "x", "text": "y"}])
    with pytest.raises(RuleFileError):
        read_rule_file(write(tmp_path / "b.json", bad))


def test_unknown_rule_set_is_rejected(tmp_path):
    with pytest.raises(RuleFileError):
        read_rule_file(write(tmp_path / "b.json", dict(BASE, rule_set="football")))


def test_duplicate_rule_number_is_rejected(tmp_path):
    bad = dict(BASE, rules=BASE["rules"] + [BASE["rules"][0]])
    with pytest.raises(RuleFileError, match="twice"):
        read_rule_file(write(tmp_path / "b.json", bad))


def test_missing_base_rule_set_is_rejected(tmp_path):
    write(tmp_path / "trial.json", TRIAL)
    with pytest.raises(RuleFileError, match="not found"):
        build_rule_sets(tmp_path)


def test_invalid_json_is_rejected(tmp_path):
    (tmp_path / "b.json").write_text("{not json", encoding="utf-8")
    with pytest.raises(RuleFileError):
        read_rule_file(tmp_path / "b.json")


def test_load_replaces_store_contents(tmp_path):
    write(tmp_path / "current.json", BASE)
    store = FakeRuleStore()
    load(store, tmp_path)
    counts = load(store, tmp_path)  # running twice must not double the rules
    assert counts[RuleSet.CURRENT] == 2


def test_bad_files_leave_store_untouched(tmp_path):
    store = FakeRuleStore()
    write(tmp_path / "current.json", BASE)
    load(store, tmp_path)
    write(tmp_path / "current.json", dict(BASE, rules=[{"text": "no number"}]))
    with pytest.raises(RuleFileError):
        load(store, tmp_path)
    assert store.count() == 2
