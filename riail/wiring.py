"""Composition root: the ONLY place that chooses which implementation sits behind each interface.

Swapping the mock AI for the real one, the keyword embedder for the AI
embedding model, or Chroma for a managed database is a change here (or in
.env), and nowhere else. A test (tests/test_architecture.py) checks that no
other component imports these concrete classes.
"""

from riail.answer.interface import Answerer
from riail.config import Config
from riail.embedding.interface import Embedder
from riail.feedback.file_log import FileFeedbackLog
from riail.query.service import QueryService
from riail.retrieval.vector_retriever import VectorRetriever
from riail.rulestore.chroma_store import ChromaRuleStore
from riail.rulestore.interface import RuleStore


def build_embedder(config: Config) -> Embedder:
    if config.embedder == "local":
        from riail.embedding.local_model import LocalModelEmbedder
        return LocalModelEmbedder()
    if config.embedder == "keyword":
        from riail.embedding.keyword import KeywordEmbedder
        return KeywordEmbedder()
    raise ValueError(f"Unknown RIAIL_EMBEDDER {config.embedder!r} (use local or keyword)")


def build_rule_store(config: Config) -> RuleStore:
    return ChromaRuleStore(embedder=build_embedder(config), path=config.db_path)


def build_answerer(config: Config) -> Answerer:
    if config.answerer == "llm":
        from riail.answer.llm_answerer import LLMAnswerer
        return LLMAnswerer(
            api_key=config.llm_api_key,
            model=config.llm_model,
            base_url=config.llm_base_url,
            timeout_seconds=config.llm_timeout_seconds,
        )
    if config.answerer in ("mock", "mock_fail"):
        from riail.answer.mock_answerer import MockAnswerer
        return MockAnswerer(mode="ok" if config.answerer == "mock" else "fail")
    raise ValueError(f"Unknown RIAIL_ANSWERER {config.answerer!r} (use llm, mock or mock_fail)")


def build_query_service(config: Config, store: RuleStore | None = None,
                        answerer: Answerer | None = None) -> tuple[QueryService, FileFeedbackLog]:
    store = store or build_rule_store(config)
    retriever = VectorRetriever(store, min_score=config.min_score, max_results=config.max_results)
    feedback = FileFeedbackLog(config.feedback_path)
    service = QueryService(retriever, answerer or build_answerer(config), feedback)
    return service, feedback
