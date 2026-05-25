from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HealthStatusDTO:
    api_status: str
    vector_store_status: str
    indexed_documents_count: int
    indexed_chunks_count: int
