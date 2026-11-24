"""RuleStore backed by a local Chroma database file (Simplified in D1 section 1.4)."""

import uuid
from datetime import date

import chromadb

from riail.embedding.interface import Embedder
from riail.models import RuleChunk, RuleSet
from riail.rulestore.interface import RuleStore

_COLLECTION = "hurling_rules"


class ChromaRuleStore(RuleStore):

    def __init__(self, embedder: Embedder, path: str | None = None):
        """`path` is the folder for the database file. None keeps it in memory (used by tests)."""
        self._embedder = embedder
        if path:
            self._client = chromadb.PersistentClient(path=path)
            self._name = _COLLECTION
        else:
            # In-memory stores share one database inside a process, so each gets its own collection.
            self._client = chromadb.EphemeralClient()
            self._name = f"{_COLLECTION}-{uuid.uuid4().hex[:8]}"
        self._collection = self._open_collection()

    def _open_collection(self):
        # embedding_function=None: vectors always come from our own Embedder,
        # so Chroma never quietly uses a different model.
        return self._client.get_or_create_collection(
            self._name,
            embedding_function=None,
            configuration={"hnsw": {"space": "cosine"}},
        )

    def add(self, chunks: list[RuleChunk]) -> None:
        if not chunks:
            return
        self._collection.upsert(
            ids=[c.id for c in chunks],
            # The title is embedded with the text so a search on "square ball" finds rule 4.10.
            embeddings=self._embedder.embed([f"{c.title}. {c.text}" for c in chunks]),
            documents=[c.text for c in chunks],
            metadatas=[
                {
                    "rule_number": c.rule_number,
                    "rule_set": c.rule_set.value,
                    "title": c.title,
                    "effective_from": c.effective_from.isoformat(),
                    "source": c.source,
                }
                for c in chunks
            ],
        )

    def clear(self) -> None:
        self._client.delete_collection(self._name)
        self._collection = self._open_collection()

    def search(self, query: str, rule_set: RuleSet, limit: int) -> list[tuple[RuleChunk, float]]:
        if self.count(rule_set) == 0:
            return []
        result = self._collection.query(
            query_embeddings=self._embedder.embed([query]),
            n_results=limit,
            where={"rule_set": rule_set.value},  # the rule-set filter happens inside the database
            include=["documents", "metadatas", "distances"],
        )
        matches = []
        for text, meta, distance in zip(
            result["documents"][0], result["metadatas"][0], result["distances"][0]
        ):
            chunk = RuleChunk(
                rule_number=meta["rule_number"],
                rule_set=RuleSet(meta["rule_set"]),
                text=text,
                effective_from=date.fromisoformat(meta["effective_from"]),
                source=meta["source"],
                title=meta.get("title", ""),
            )
            # Cosine distance runs from 0 (same) to 2 (opposite); turn it into a 0-1 score.
            score = max(0.0, 1.0 - distance)
            matches.append((chunk, score))
        return matches

    def count(self, rule_set: RuleSet | None = None) -> int:
        if rule_set is None:
            return self._collection.count()
        found = self._collection.get(where={"rule_set": rule_set.value}, include=[])
        return len(found["ids"])
