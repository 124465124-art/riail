"""Query function: runs one question from start to finish (Built in D1 section 1.4).

1. Ask the Retriever for matching rules from the chosen rule set.
2. No rules: answer "not covered" and never call the AI.
3. Ask the Answerer to explain the rules.
4. If the AI fails in any way: show the matching rules without an explanation.

It only knows the Retriever, Answerer and FeedbackLog interfaces, never the
classes behind them, so each can be swapped without changing this file.
"""

import logging
import uuid
from dataclasses import replace

from riail.answer.interface import Answerer, AnswererError
from riail.feedback.interface import FeedbackLog
from riail.models import Answer, AnswerStatus, RuleSet
from riail.retrieval.interface import Retriever

log = logging.getLogger(__name__)


class QueryService:

    def __init__(self, retriever: Retriever, answerer: Answerer, feedback: FeedbackLog):
        self._retriever = retriever
        self._answerer = answerer
        self._feedback = feedback

    def ask(self, question: str, rule_set: RuleSet) -> Answer:
        rules = self._retriever.search(question, rule_set)

        if not rules:
            answer = Answer(status=AnswerStatus.NOT_COVERED, rule_set=rule_set)
        else:
            try:
                answer = self._answerer.answer(question, rules)
            except AnswererError as e:
                answer = self._fallback(rules, rule_set, "ai_error", str(e))
            except Exception as e:  # an unexpected bug in the AI component must not crash the app
                log.exception("Unexpected error in the answerer")
                answer = self._fallback(rules, rule_set, "ai_unexpected_error", type(e).__name__)

            if answer.rule_set != rule_set:
                # Defence in depth for the "wrong rule set" risk: never show another rule set's answer.
                answer = self._fallback(rules, rule_set, "rule_set_mismatch", answer.rule_set.value)

        answer = replace(answer, answer_id=uuid.uuid4().hex)
        self._feedback.record_answer(answer)
        return answer

    def _fallback(self, rules, rule_set: RuleSet, kind: str, detail: str) -> Answer:
        self._feedback.record_error(kind, detail)
        return Answer(status=AnswerStatus.FALLBACK, rule_set=rule_set, rules=rules)
