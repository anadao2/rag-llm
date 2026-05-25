from __future__ import annotations

from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    """Schema de request para endpoint /ingest."""

    docs_dir: str | None = Field(default=None, description="Diretório dos documentos")
    chunk_size: int | None = Field(default=None, ge=100, description="Tamanho do chunk")
    chunk_overlap: int | None = Field(default=None, ge=0, description="Sobreposição entre chunks")
    embedding_model: str | None = Field(default=None, description="Modelo de embedding")


class IngestResponse(BaseModel):
    """Schema de response do endpoint /ingest."""

    documents_count: int = Field(description="Quantidade de documentos processados")
    chunks_count: int = Field(description="Quantidade de chunks gerados")


class HealthResponse(BaseModel):
    """Schema de response do endpoint /health."""

    api_status: str = Field(description="Status da API")
    vector_store_status: str = Field(description="Status do armazenamento vetorial")
    indexed_documents_count: int = Field(description="Quantidade de documentos indexados")
