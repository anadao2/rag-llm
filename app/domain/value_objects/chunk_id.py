from __future__ import annotations

from dataclasses import dataclass

from app.domain.value_objects.document_id import DocumentId


@dataclass(frozen=True, slots=True)
class ChunkId:
    """Identificador tipado para Chunk (composto por doc_id + ordem)."""

    value: str

    def __post_init__(self) -> None:
        if not self.value or not isinstance(self.value, str):
            raise ValueError("ChunkId must be a non-empty string")

    @classmethod
    def generate(cls, doc_id: DocumentId, order: int) -> ChunkId:
        return cls(value=f"{doc_id.value}:{order}")

    @classmethod
    def from_string(cls, value: str) -> ChunkId:
        return cls(value=value)

    def extract_document_id(self) -> DocumentId:
        """Extrai o DocumentId do ChunkId."""
        parts = self.value.rsplit(":", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid ChunkId format: {self.value}")
        return DocumentId.from_string(parts[0])

    def __str__(self) -> str:
        return self.value
