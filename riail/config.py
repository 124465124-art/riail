"""Settings, read from environment variables (and a local .env file).

The API key lives only in .env, which .gitignore keeps out of the repository,
and it is never sent to the browser (D1 risk: "the AI service key is leaked").
"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    answerer: str = "mock"            # mock (no key needed) | llm | mock_fail
    llm_api_key: str = ""
    llm_model: str = "openai/gpt-oss-20b"
    llm_base_url: str = "https://api.groq.com/openai/v1"
    llm_timeout_seconds: float = 15.0
    embedder: str = "local"           # local (AI embedding model) | keyword (no model, offline)
    min_score: float = 0.3
    max_results: int = 4
    db_path: str = "instance/chroma"
    rules_dir: str = "data/rules"
    feedback_path: str = "instance/feedback.jsonl"
    max_question_length: int = 500

    @classmethod
    def from_env(cls) -> "Config":
        load_dotenv()
        e = os.environ.get
        d = cls()
        return cls(
            answerer=e("RIAIL_ANSWERER", d.answerer),
            llm_api_key=e("RIAIL_LLM_API_KEY", ""),
            llm_model=e("RIAIL_LLM_MODEL", d.llm_model),
            llm_base_url=e("RIAIL_LLM_BASE_URL", d.llm_base_url),
            llm_timeout_seconds=float(e("RIAIL_LLM_TIMEOUT", d.llm_timeout_seconds)),
            embedder=e("RIAIL_EMBEDDER", d.embedder),
            min_score=float(e("RIAIL_MIN_SCORE", d.min_score)),
            max_results=int(e("RIAIL_MAX_RESULTS", d.max_results)),
            db_path=e("RIAIL_DB_PATH", d.db_path),
            rules_dir=e("RIAIL_RULES_DIR", d.rules_dir),
            feedback_path=e("RIAIL_FEEDBACK_PATH", d.feedback_path),
            max_question_length=int(e("RIAIL_MAX_QUESTION_LENGTH", d.max_question_length)),
        )
