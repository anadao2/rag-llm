from __future__ import annotations

from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    docs_dir: str | None = None
    chunk_size: int | None = Field(default=None, gt=0)
    chunk_overlap: int | None = Field(default=None, ge=0)
    embedding_model: str | None = None


class IngestResponse(BaseModel):
    documents_count: int
    chunks_count: int


class HealthResponse(BaseModel):
    api_status: str
    vector_store_status: str
    indexed_documents_count: int
