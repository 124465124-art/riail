"""FeedbackLog that appends one JSON line per event to a local file (Simplified)."""

import json
import threading
from datetime import datetime, timezone
from pathlib import Path

from riail.feedback.interface import RATINGS, FeedbackLog
from riail.models import Answer


class FileFeedbackLog(FeedbackLog):

    def __init__(self, path: str):
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()  # Flask can handle two requests at once

    def record_answer(self, answer: Answer) -> None:
        self._write({
            "event": "answer",
            "answer_id": answer.answer_id,
            "status": answer.status.value,
            "rule_set": answer.rule_set.value,
            "citations": answer.citations,
        })

    def record_rating(self, answer_id: str, rating: str) -> None:
        if rating not in RATINGS:
            raise ValueError(f"Rating must be one of {RATINGS}")
        if not answer_id:
            raise ValueError("A rating needs an answer id")
        self._write({"event": "rating", "answer_id": answer_id, "rating": rating})

    def record_error(self, kind: str, detail: str) -> None:
        self._write({"event": "error", "kind": kind, "detail": detail[:300]})

    def read_all(self) -> list[dict]:
        """Every saved event (used by tests and for reviewing feedback)."""
        if not self._path.exists():
            return []
        with self._path.open(encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]

    def _write(self, event: dict) -> None:
        event["time"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with self._lock, self._path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")
