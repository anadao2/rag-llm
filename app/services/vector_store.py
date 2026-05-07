from __future__ import annotations

import json
from pathlib import Path
from threading import Lock
from typing import Any

import faiss
import numpy as np

from app.core.config import settings
from app.schemas.documents import EmbeddedChunk


class FaissVectorStore:
    """Small FAISS adapter with local persistence."""

    def __init__(
        self,
        base_dir: Path | str = settings.faiss_dir,
        index_file: str = settings.faiss_index_file,
        metadata_file: str = settings.faiss_metadata_file,
    ) -> None:
        self.base_dir = Path(base_dir)
        self.index_path = self.base_dir / index_file
        self.metadata_path = self.base_dir / metadata_file
        self._lock = Lock()
        self._index: faiss.Index | None = None
        self._metadata: list[dict[str, Any]] = []
        self._load()

    def add_embeddings(self, chunks: list[EmbeddedChunk]) -> int:
        if not chunks:
            return 0

        vectors = np.array([chunk.embedding for chunk in chunks], dtype=np.float32)
        if vectors.ndim != 2:
            raise ValueError("Invalid embedding matrix shape")

        with self._lock:
            if self._index is None:
                self._index = faiss.IndexFlatL2(vectors.shape[1])
            self._index.add(vectors)
            self._metadata.extend(
                {
                    "chunk_id": chunk.chunk_id,
                    "doc_id": chunk.doc_id,
                    "text": chunk.text,
                    "metadata": chunk.metadata,
                }
                for chunk in chunks
            )
            self._save()
        return len(chunks)

    def health(self) -> dict[str, Any]:
        return {
            "ready": self._index is not None,
            "indexed_chunks": len(self._metadata),
        }

    def indexed_document_count(self) -> int:
        return len({item["doc_id"] for item in self._metadata})

    def _load(self) -> None:
        self.base_dir.mkdir(parents=True, exist_ok=True)
        if self.index_path.exists():
            self._index = faiss.read_index(str(self.index_path))
        if self.metadata_path.exists():
            self._metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))

    def _save(self) -> None:
        if self._index is not None:
            faiss.write_index(self._index, str(self.index_path))
        self.metadata_path.write_text(json.dumps(self._metadata, ensure_ascii=True, indent=2), encoding="utf-8")
