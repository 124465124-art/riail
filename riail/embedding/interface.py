"""Embedder interface: turns text into vectors so similar meanings can be found.

Target: an embedding API. Prototype: a free model that runs locally
(Simplified). Only the RuleStore uses this.
"""

from abc import ABC, abstractmethod


class Embedder(ABC):

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one vector per text, in the same order. All vectors have the same length."""
