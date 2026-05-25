from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass(frozen=True, slots=True)
class IngestRequestDTO:
    """DTO para entrada do caso de uso de ingestão."""

    docs_dir: Path
    chunk_size: int
    chunk_overlap: int
    embedding_model: str


@dataclass(frozen=True, slots=True)
class IngestResultDTO:
    """DTO para saída do caso de uso de ingestão."""

    documents_count: int
    chunks_count: int
    processed_document_ids: List[str]
