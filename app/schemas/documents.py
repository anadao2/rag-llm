from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ParsedDocument:
    """Structured representation of a source document."""

    doc_id: str
    source_path: str
    file_name: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ChunkedDocument:
    """A text chunk produced from a parsed document."""

    chunk_id: str
    doc_id: str
    text: str
    order: int
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class EmbeddedChunk:
    """Chunk plus vector embedding, ready for FAISS ingestion."""

    chunk_id: str
    doc_id: str
    text: str
    embedding: list[float]
    metadata: dict[str, Any] = field(default_factory=dict)
