"""Checks that components only talk to each other through interfaces.

Concrete classes (Chroma store, LLM answerer, mock, local model, file log)
may only be imported by the composition root (riail/wiring.py). If someone
makes the query function import the LLM answerer directly, this test fails.
"""

import ast
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent.parent / "riail"

CONCRETE_MODULES = {
    "riail.rulestore.chroma_store",
    "riail.answer.llm_answerer",
    "riail.answer.mock_answerer",
    "riail.embedding.local_model",
    "riail.embedding.keyword",
    "riail.feedback.file_log",
    "riail.retrieval.vector_retriever",
}

# Each concrete module may import its own component's helpers; wiring.py may import anything.
ALLOWED = {"riail/wiring.py"}


def imports_of(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module)
        elif isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
    return found


def test_only_the_composition_root_imports_concrete_implementations():
    offenders = []
    for path in PACKAGE.rglob("*.py"):
        rel = path.relative_to(PACKAGE.parent).as_posix()
        if rel in ALLOWED:
            continue
        own_component = rel.split("/")[1]
        for module in imports_of(path) & CONCRETE_MODULES:
            if module.split(".")[1] != own_component:
                offenders.append(f"{rel} imports {module}")
    assert offenders == []


def test_ai_calls_only_happen_in_the_answer_component():
    for path in PACKAGE.rglob("*.py"):
        rel = path.relative_to(PACKAGE.parent).as_posix()
        if "requests" in imports_of(path):
            assert rel.startswith("riail/answer/"), f"{rel} makes HTTP calls outside the AI component"
