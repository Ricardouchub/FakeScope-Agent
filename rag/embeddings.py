from __future__ import annotations

from typing import Iterable, List

from sentence_transformers import SentenceTransformer


class EmbeddingService:
    def __init__(self, model_name: str = "BAAI/bge-m3") -> None:
        self._model = SentenceTransformer(model_name)

    def embed_documents(self, texts: Iterable[str]) -> List[List[float]]:
        return self._model.encode(list(texts), convert_to_numpy=False)

    def embed_query(self, text: str) -> List[float]:
        return self._model.encode([text], convert_to_numpy=False)[0]


__all__ = ["EmbeddingService"]
