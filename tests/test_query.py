from riail.answer.interface import Answerer
from riail.answer.mock_answerer import MockAnswerer
from riail.feedback.file_log import FileFeedbackLog
from riail.models import Answer, AnswerStatus, RuleSet
from riail.query.service import QueryService
from riail.retrieval.vector_retriever import VectorRetriever
from tests.conftest import FakeRuleStore, make_rule

QUESTION = "Joe Bloggs took six steps with the ball"


def make_service(tmp_path, answerer, scored=((make_rule("4.1"), 0.9),)):
    feedback = FileFeedbackLog(str(tmp_path / "feedback.jsonl"))
    retriever = VectorRetriever(FakeRuleStore(list(scored)), min_score=0.3)
    return QueryService(retriever, answerer, feedback), feedback


def test_matching_rules_and_working_ai_give_ok_answer(tmp_path):
    service, _ = make_service(tmp_path, MockAnswerer("ok"))
    answer = service.ask(QUESTION, RuleSet.CURRENT)
    assert answer.status is AnswerStatus.OK
    assert answer.citations == ["4.1"]
    assert answer.answer_id


def test_no_matching_rules_gives_not_covered_and_ai_is_never_called(tmp_path):
    mock = MockAnswerer("ok")
    service, _ = make_service(tmp_path, mock, scored=[(make_rule("4.1"), 0.05)])
    answer = service.ask("Who won the 1990 World Cup?", RuleSet.CURRENT)
    assert answer.status is AnswerStatus.NOT_COVERED
    assert mock.calls == []


def test_ai_error_gives_matching_rules_instead(tmp_path):
    service, feedback = make_service(tmp_path, MockAnswerer("fail"))
    answer = service.ask(QUESTION, RuleSet.CURRENT)
    assert answer.status is AnswerStatus.FALLBACK
    assert [r.rule_number for r in answer.rules] == ["4.1"]
    assert answer.text == ""
    assert any(e["event"] == "error" for e in feedback.read_all())


def test_invented_citation_falls_back_instead_of_showing_it(tmp_path):
    service, _ = make_service(tmp_path, MockAnswerer("invented_citation"))
    assert service.ask(QUESTION, RuleSet.CURRENT).status is AnswerStatus.FALLBACK


def test_unexpected_crash_in_ai_component_still_falls_back(tmp_path):
    class BrokenAnswerer(Answerer):
        def answer(self, question, rules):
            raise RuntimeError("bug")

    service, _ = make_service(tmp_path, BrokenAnswerer())
    assert service.ask(QUESTION, RuleSet.CURRENT).status is AnswerStatus.FALLBACK


def test_answer_for_wrong_rule_set_is_never_shown(tmp_path):
    class WrongSetAnswerer(Answerer):
        def answer(self, question, rules):
            return Answer(status=AnswerStatus.OK, rule_set=RuleSet.TRIAL_2026, text="x", citations=["4.1"])

    service, _ = make_service(tmp_path, WrongSetAnswerer())
    answer = service.ask(QUESTION, RuleSet.CURRENT)
    assert answer.status is AnswerStatus.FALLBACK and answer.rule_set is RuleSet.CURRENT


def test_question_text_is_never_written_to_the_log(tmp_path):
    service, feedback = make_service(tmp_path, MockAnswerer("fail"))
    service.ask(QUESTION, RuleSet.CURRENT)
    log_text = (tmp_path / "feedback.jsonl").read_text()
    assert "Joe Bloggs" not in log_text
    assert "six steps" not in log_text
