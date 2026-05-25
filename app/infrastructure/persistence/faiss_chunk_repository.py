from __future__ import annotations

import json
from pathlib import Path
from threading import Lock
from typing import Any, List

import faiss
import numpy as np

from app.domain.entities.chunk import Chunk
from app.domain.repositories.chunk_repository import ChunkRepository
from app.domain.value_objects.chunk_id import ChunkId
from app.domain.value_objects.document_id import DocumentId
from app.domain.value_objects.embedding import Embedding
from app.infrastructure.persistence.mappers.chunk_mapper import ChunkMapper


class FaissChunkRepository(ChunkRepository):
    """
    Adapter - Implementação concreta usando FAISS para vetores
    e JSON para metadados.
    """

    def __init__(
        self,
        base_dir: Path,
        index_file: str = "index.faiss",
        metadata_file: str = "chunks_metadata.json",
    ) -> None:
        self.base_dir = Path(base_dir)
        self.index_path = self.base_dir / index_file
        self.metadata_path = self.base_dir / metadata_file
        self._lock = Lock()
        self._index: faiss.Index | None = None
        self._metadata: List[Dict[str, Any]] = []
        self._mapper = ChunkMapper()
        self._load()

    def save(self, chunk: Chunk) -> None:
        self.save_batch([chunk])

    def save_batch(self, chunks: List[Chunk]) -> None:
        if not chunks:
            return

        # Validar que todos têm embedding
        for chunk in chunks:
            if not chunk.has_embedding():
                raise ValueError(f"Chunk {chunk.chunk_id} has no embedding")

        vectors = np.array(
            [chunk.embedding.to_numpy() for chunk in chunks],
            dtype=np.float32,
        )

        with self._lock:
            if self._index is None:
                self._index = faiss.IndexFlatL2(vectors.shape[1])
            self._index.add(vectors)

            for chunk in chunks:
                self._metadata.append(self._mapper.to_record(chunk))

            self._save()

    def find_by_id(self, chunk_id: ChunkId) -> Chunk | None:
        for record in self._metadata:
            if record["chunk_id"] == str(chunk_id):
                return self._mapper.to_domain(record)
        return None

    def find_by_document_id(self, doc_id: DocumentId) -> List[Chunk]:
        results = []
        for record in self._metadata:
            if record["doc_id"] == str(doc_id):
                results.append(self._mapper.to_domain(record))
        return results

    def search_similar(
        self,
        query_embedding: List[float],
        top_k: int = 5,
    ) -> List[Chunk]:
        if self._index is None or self._index.ntotal == 0:
            return []

        query = np.array([query_embedding], dtype=np.float32)
        distances, indices = self._index.search(query, top_k)

        results = []
        for idx in indices[0]:
            if 0 <= idx < len(self._metadata):
                results.append(self._mapper.to_domain(self._metadata[idx]))
        return results

    def count(self) -> int:
        return len(self._metadata)

    def is_ready(self) -> bool:
        return self._index is not None and self._index.ntotal > 0

    def _load(self) -> None:
        self.base_dir.mkdir(parents=True, exist_ok=True)
        if self.index_path.exists():
            self._index = faiss.read_index(str(self.index_path))
        if self.metadata_path.exists():
            content = self.metadata_path.read_text(encoding="utf-8")
            self._metadata = json.loads(content)

    def _save(self) -> None:
        if self._index is not None:
            faiss.write_index(self._index, str(self.index_path))
        self.metadata_path.write_text(
            json.dumps(self._metadata, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )
