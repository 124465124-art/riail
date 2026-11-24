import pytest

from riail.feedback.file_log import FileFeedbackLog
from riail.models import Answer, AnswerStatus, RuleSet


def test_rating_is_saved(tmp_path):
    log = FileFeedbackLog(str(tmp_path / "f.jsonl"))
    log.record_rating("abc", "up")
    [event] = log.read_all()
    assert event["event"] == "rating" and event["answer_id"] == "abc" and event["rating"] == "up"
    assert "time" in event


@pytest.mark.parametrize("rating", ["", "5 stars", None, "UP"])
def test_invalid_rating_is_rejected(tmp_path, rating):
    with pytest.raises(ValueError):
        FileFeedbackLog(str(tmp_path / "f.jsonl")).record_rating("abc", rating)


def test_answer_record_holds_no_question_or_explanation_text(tmp_path):
    log = FileFeedbackLog(str(tmp_path / "f.jsonl"))
    log.record_answer(Answer(status=AnswerStatus.OK, rule_set=RuleSet.CURRENT,
                             text="Secret explanation", citations=["4.1"], answer_id="abc"))
    [event] = log.read_all()
    assert set(event) == {"event", "answer_id", "status", "rule_set", "citations", "time"}


def test_long_error_detail_is_cut_short(tmp_path):
    log = FileFeedbackLog(str(tmp_path / "f.jsonl"))
    log.record_error("ai_error", "x" * 1000)
    assert len(log.read_all()[0]["detail"]) == 300


def test_missing_folder_is_created(tmp_path):
    FileFeedbackLog(str(tmp_path / "new" / "f.jsonl")).record_error("k", "d")
    assert (tmp_path / "new" / "f.jsonl").exists()
