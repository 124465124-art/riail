"""Keyword embedder: a simple word-count vector with no AI model.

Used for three things:
- unit tests, because it is fast, needs no download and always gives the same result;
- running the app offline (RIAIL_EMBEDDER=keyword);
- the keyword-search baseline planned in D1 section 1.6, to compare against the AI.

It only matches shared words, so "he threw it" will not find a rule that says
"throwing the ball" unless the words overlap. That weakness is the point of
the comparison.
"""

import hashlib
import math
import re

from riail.embedding.interface import Embedder

_STOP_WORDS = {
    "a", "an", "and", "the", "is", "it", "of", "to", "in", "on", "or", "for",
    "with", "be", "was", "if", "at", "by", "he", "she", "they", "that", "this",
    "can", "what", "does", "do", "i", "his", "her", "their", "from", "as",
}


def _words(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [w for w in words if w not in _STOP_WORDS]


class KeywordEmbedder(Embedder):

    def __init__(self, size: int = 4096):
        self._size = size

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text: str) -> list[float]:
        vector = [0.0] * self._size
        for word in _words(text):
            # A stable hash, so the same word always lands in the same slot.
            slot = int(hashlib.md5(word.encode()).hexdigest(), 16) % self._size
            vector[slot] += 1.0
        length = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [v / length for v in vector]
