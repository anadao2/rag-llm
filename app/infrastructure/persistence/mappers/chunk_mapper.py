from __future__ import annotations

from typing import Any, Dict, List

from app.domain.entities.chunk import Chunk
from app.domain.value_objects.chunk_id import ChunkId
from app.domain.value_objects.document_id import DocumentId
from app.domain.value_objects.embedding import Embedding


class ChunkMapper:
    """
    Mapper - Traduz entre Chunk (Domain) e dict (Persistence Model).
    """

    def to_record(self, chunk: Chunk) -> Dict[str, Any]:
        """Converte Chunk para formato de persistência."""
        record: Dict[str, Any] = {
            "chunk_id": str(chunk.chunk_id),
            "doc_id": str(chunk.doc_id),
            "text": chunk.text,
            "order": chunk.order,
            "metadata": chunk.metadata,
        }

        if chunk.has_embedding():
            record["embedding"] = list(chunk.embedding.vector)
            record["embedding_model"] = chunk.embedding.model
            record["embedding_dimensions"] = chunk.embedding.dimensions

        return record

    def to_domain(self, record: Dict[str, Any]) -> Chunk:
        """Converte registro de persistência para Chunk."""
        chunk = Chunk(
            chunk_id=ChunkId.from_string(record["chunk_id"]),
            doc_id=DocumentId.from_string(record["doc_id"]),
            text=record["text"],
            order=record["order"],
            metadata=record.get("metadata", {}),
        )

        # Restaurar embedding se existir
        if "embedding" in record:
            embedding = Embedding(
                vector=tuple(record["embedding"]),
                model=record.get("embedding_model", "unknown"),
                dimensions=record.get("embedding_dimensions", len(record["embedding"])),
            )
            chunk.attach_embedding(embedding)

        return chunk

    def to_record_list(self, chunks: List[Chunk]) -> List[Dict[str, Any]]:
        return [self.to_record(chunk) for chunk in chunks]

    def to_domain_list(self, records: List[Dict[str, Any]]) -> List[Chunk]:
        return [self.to_domain(record) for record in records]
