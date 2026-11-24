"""Mock Answerer: returns realistic fixed replies through the same interface.

Mocked in D1 section 1.4 ("LLM in tests"). Used for:
- unit tests, so results are the same every run and cost nothing;
- running the app without an API key (RIAIL_ANSWERER=mock);
- showing the AI-failure fallback on demand (RIAIL_ANSWERER=mock_fail).
"""

from riail.answer.citations import check_citations
from riail.answer.interface import Answerer, AnswererError
from riail.models import Answer, AnswerStatus, RuleChunk


class MockAnswerer(Answerer):

    MODES = ("ok", "fail", "no_citations", "invented_citation", "not_covered")

    def __init__(self, mode: str = "ok"):
        if mode not in self.MODES:
            raise ValueError(f"Unknown mock mode {mode!r}; choose from {self.MODES}")
        self.mode = mode
        self.calls = []  # (question, rules) for each call, so tests can check what was sent

    def answer(self, question: str, rules: list[RuleChunk]) -> Answer:
        self.calls.append((question, rules))
        if not rules:
            raise AnswererError("No rules were given to answer from")
        if self.mode == "fail":
            raise AnswererError("Mock AI failure (simulated outage)")
        if self.mode == "not_covered":
            return Answer(status=AnswerStatus.NOT_COVERED, rule_set=rules[0].rule_set)

        # Shaped like a real reply, then put through the same checks as the real one.
        top = rules[0]
        cited = {
            "ok": [top.rule_number],
            "no_citations": [],
            "invented_citation": [top.rule_number, "99.9"],
        }[self.mode]
        citations = check_citations(cited, rules)
        return Answer(
            status=AnswerStatus.OK,
            rule_set=top.rule_set,
            text=(
                f"[Mock AI answer] The most relevant rule is {top.rule_number} "
                f"({top.title}). {top.text}"
            ),
            citations=citations,
            rules=[top],
        )
