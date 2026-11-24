"""Citation checks shared by every Answerer.

These checks are the main mitigation for the top D1 risk, "the AI makes up a
rule or explains a rule wrongly". An answer is only accepted if it cites at
least one rule and every rule it cites was actually given to the AI.
"""

from riail.answer.interface import AnswererError
from riail.models import RuleChunk


def check_citations(citations: list[str], rules: list[RuleChunk]) -> list[str]:
    """Return the citations, cleaned up, or raise AnswererError if they cannot be trusted."""
    cleaned = []
    for c in citations:
        if not isinstance(c, str) or not c.strip():
            raise AnswererError("A citation is not a rule number")
        c = c.strip()
        if c.lower().startswith("rule "):
            c = c[5:].strip()
        if c not in cleaned:
            cleaned.append(c)

    if not cleaned:
        raise AnswererError("The answer did not cite any rule")

    allowed = {rule.rule_number for rule in rules}
    invented = [c for c in cleaned if c not in allowed]
    if invented:
        raise AnswererError(f"The answer cited rules that were not retrieved: {invented}")
    return cleaned
