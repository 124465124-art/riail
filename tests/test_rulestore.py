from riail.embedding.keyword import KeywordEmbedder
from riail.models import RuleSet
from riail.rulestore.chroma_store import ChromaRuleStore
from tests.conftest import make_rule


def new_store():
    return ChromaRuleStore(embedder=KeywordEmbedder())


def test_added_rules_can_be_counted_per_rule_set():
    store = new_store()
    store.add([make_rule("1.7"), make_rule("4.1"), make_rule("T1", rule_set=RuleSet.TRIAL_2026)])
    assert store.count() == 3
    assert store.count(RuleSet.CURRENT) == 2
    assert store.count(RuleSet.TRIAL_2026) == 1


def test_adding_same_rule_again_replaces_it():
    store = new_store()
    store.add([make_rule("4.1", text="Old wording")])
    store.add([make_rule("4.1", text="New wording about steps")])
    assert store.count() == 1
    [(chunk, _)] = store.search("steps", RuleSet.CURRENT, limit=5)
    assert chunk.text == "New wording about steps"


def test_search_never_returns_another_rule_set():
    store = new_store()
    store.add([
        make_rule("1.7", text="Carry the ball for four steps", rule_set=RuleSet.CURRENT),
        make_rule("1.7", text="Carry the ball for six steps", rule_set=RuleSet.TRIAL_2026),
    ])
    results = store.search("how many steps can you carry the ball", RuleSet.CURRENT, limit=5)
    assert [c.rule_set for c, _ in results] == [RuleSet.CURRENT]
    assert "four" in results[0][0].text


def test_search_returns_best_match_first_with_scores_between_0_and_1():
    store = new_store()
    store.add([
        make_rule("2.8", title="Sideline puck", text="Ball over the sideline gives a sideline puck"),
        make_rule("4.1", title="Overcarrying", text="Carrying the ball too many steps is a foul"),
    ])
    results = store.search("too many steps carrying", RuleSet.CURRENT, limit=5)
    assert results[0][0].rule_number == "4.1"
    assert all(0 <= score <= 1 for _, score in results)
    assert results[0][1] > results[1][1]


def test_search_of_empty_rule_set_returns_nothing():
    store = new_store()
    store.add([make_rule("4.1")])
    assert store.search("steps", RuleSet.TRIAL_2026, limit=5) == []


def test_clear_removes_everything():
    store = new_store()
    store.add([make_rule("4.1")])
    store.clear()
    assert store.count() == 0


def test_rule_comes_back_with_all_its_fields():
    store = new_store()
    original = make_rule("4.10", title="Square ball", text="Attacker in the small rectangle before the ball")
    store.add([original])
    [(chunk, _)] = store.search("square ball", RuleSet.CURRENT, limit=1)
    assert chunk == original
