"""Tests for the two routes, using Flask's test client with the mock AI and keyword vectors."""

import pytest

from app import create_app
from riail.answer.mock_answerer import MockAnswerer
from riail.config import Config


@pytest.fixture
def client(tmp_path, loaded_store):
    config = Config(answerer="mock", embedder="keyword", min_score=0.1,
                    feedback_path=str(tmp_path / "feedback.jsonl"), max_question_length=500)
    return create_app(config, store=loaded_store, answerer=MockAnswerer("ok")).test_client()


def ask(client, question="He took too many steps carrying the ball", rule_set="current"):
    return client.post("/ask", json={"question": question, "rule_set": rule_set})


def test_valid_question_returns_answer_in_agreed_shape(client):
    res = ask(client)
    assert res.status_code == 200
    data = res.get_json()
    assert set(data) >= {"answer_id", "status", "rule_set", "answer", "citations", "rules"}
    assert data["status"] == "ok"
    assert data["rule_set"] == "current"


@pytest.mark.parametrize("question", ["", "    ", None, 42])
def test_empty_or_missing_question_is_rejected(client, question):
    res = client.post("/ask", json={"question": question, "rule_set": "current"})
    assert res.status_code == 400
    assert "question" in res.get_json()["error"].lower()


def test_very_long_question_is_rejected(client):
    assert ask(client, question="steps " * 200).status_code == 400


def test_unknown_rule_set_is_rejected(client):
    assert ask(client, rule_set="football").status_code == 400


def test_non_json_body_is_rejected(client):
    assert client.post("/ask", data="question=hi").status_code == 400


def test_trial_rule_set_is_kept_in_answer(client):
    data = ask(client, "two handpasses in a row consecutive", "trial_2026").get_json()
    assert data["rule_set"] == "trial_2026"
    assert all("TRIAL" in r["text"] or r["rule_number"][0].isdigit() for r in data["rules"])


def test_feedback_is_accepted_for_an_answer(client):
    answer_id = ask(client).get_json()["answer_id"]
    res = client.post("/feedback", json={"answer_id": answer_id, "rating": "up"})
    assert res.status_code == 200 and res.get_json() == {"ok": True}


@pytest.mark.parametrize("body", [{"answer_id": "x", "rating": "meh"}, {"rating": "up"}, {"answer_id": "x" * 100, "rating": "up"}])
def test_bad_feedback_is_rejected(client, body):
    assert client.post("/feedback", json=body).status_code == 400


def test_home_page_is_served(client):
    res = client.get("/")
    assert res.status_code == 200 and b"Riail" in res.data


def test_api_key_never_reaches_the_browser(tmp_path, loaded_store):
    config = Config(answerer="mock", embedder="keyword", llm_api_key="sk-secret-123",
                    feedback_path=str(tmp_path / "f.jsonl"))
    c = create_app(config, store=loaded_store, answerer=MockAnswerer("fail")).test_client()
    for res in (c.get("/"), ask(c)):
        assert b"sk-secret-123" not in res.data
