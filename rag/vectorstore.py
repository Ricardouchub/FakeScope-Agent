from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Sequence

import chromadb
from chromadb.config import Settings

from config.settings import get_settings


class VectorStoreManager:
    def __init__(self, collection_name: str = "fakescope") -> None:
        settings = get_settings()
        persist_dir = Path(settings.storage.persist_directory)
        persist_dir.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.Client(Settings(chroma_db_impl="duckdb+parquet", persist_directory=str(persist_dir)))
        self._collection = self._client.get_or_create_collection(collection_name)

    def add_texts(self, ids: Sequence[str], texts: Sequence[str], metadatas: Sequence[dict] | None = None) -> None:
        self._collection.add(ids=list(ids), documents=list(texts), metadatas=list(metadatas) if metadatas else None)

    def similarity_search(self, query: str, k: int = 5) -> List[dict]:
        result = self._collection.query(query_texts=[query], n_results=k)
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        ids = result.get("ids", [[]])[0]
        return [
            {
                "id": doc_id,
                "document": doc,
                "metadata": metadata or {},
            }
            for doc_id, doc, metadata in zip(ids, documents, metadatas)
        ]

    def reset(self) -> None:
        self._collection.delete()


__all__ = ["VectorStoreManager"]
