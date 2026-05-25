from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.domain.value_objects.chunk_id import ChunkId
from app.domain.value_objects.document_id import DocumentId
from app.domain.value_objects.embedding import Embedding


@dataclass
class Chunk:
    """
    Entidade Chunk - identidade única (chunk_id composto).
    Pode receber embedding após processamento.
    """

    chunk_id: ChunkId
    doc_id: DocumentId
    text: str
    order: int
    metadata: dict[str, Any] = field(default_factory=dict)
    embedding: Embedding | None = None

    def __post_init__(self) -> None:
        if not self.text:
            raise ValueError("text cannot be empty")
        if self.order < 0:
            raise ValueError("order must be non-negative")

    @classmethod
    def create(
        cls,
        doc_id: DocumentId,
        text: str,
        order: int,
        start_char: int,
        end_char: int,
        file_name: str,
        source_path: str,
    ) -> Chunk:
        """Factory method para criar novo chunk."""
        chunk_id = ChunkId.generate(doc_id, order)
        metadata = {
            "file_name": file_name,
            "source_path": source_path,
            "start_char": start_char,
            "end_char": end_char,
        }
        return cls(
            chunk_id=chunk_id,
            doc_id=doc_id,
            text=text,
            order=order,
            metadata=metadata,
        )

    def attach_embedding(self, embedding: Embedding) -> None:
        """Anexa embedding ao chunk após processamento."""
        self.embedding = embedding

    def has_embedding(self) -> bool:
        return self.embedding is not None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Chunk):
            return False
        return self.chunk_id == other.chunk_id

    def __hash__(self) -> int:
        return hash(self.chunk_id)
