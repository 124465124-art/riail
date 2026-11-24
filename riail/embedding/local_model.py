"""Local embedding model (all-MiniLM-L6-v2, run with ONNX).

This is the "free model that runs on a computer" from D1 section 1.4. Chroma
ships it, so no PyTorch install is needed. The model (about 80 MB) downloads
once, the first time it is used, and is then cached on disk.
"""

from riail.embedding.interface import Embedder


class LocalModelEmbedder(Embedder):

    def __init__(self):
        # Imported here so the rest of the app (and the tests) do not need the model.
        from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2

        self._model = ONNXMiniLM_L6_V2()

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [list(map(float, vector)) for vector in self._model(texts)]
