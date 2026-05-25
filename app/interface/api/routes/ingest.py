from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.application.dto.ingest_dto import IngestRequestDTO, IngestResultDTO
from app.application.use_cases.ingest_documents import IngestDocumentsUseCase
from app.application.use_cases.get_health_status import GetHealthStatusUseCase
from app.core.config import settings
from app.infrastructure.external.openai_embedder import OpenAIEmbedder
from app.infrastructure.persistence.faiss_chunk_repository import FaissChunkRepository
from app.infrastructure.persistence.json_document_repository import JsonDocumentRepository
from app.interface.api.schemas.ingest_schemas import HealthResponse, IngestRequest, IngestResponse

router = APIRouter(tags=["ingest"])


def _create_use_cases() -> tuple[IngestDocumentsUseCase, GetHealthStatusUseCase]:
    """Factory - Cria instâncias de use cases com dependências injetadas."""
    doc_repo = JsonDocumentRepository(base_dir=settings.faiss_dir)
    chunk_repo = FaissChunkRepository(base_dir=settings.faiss_dir)
    embedder = OpenAIEmbedder(api_key=settings.openai_api_key)

    ingest_uc = IngestDocumentsUseCase(
        document_repo=doc_repo,
        chunk_repo=chunk_repo,
        embedding_client=embedder,
    )
    health_uc = GetHealthStatusUseCase(
        document_repo=doc_repo,
        chunk_repo=chunk_repo,
    )

    return ingest_uc, health_uc


@router.post("/ingest", response_model=IngestResponse)
def ingest_documents(payload: IngestRequest | None = None) -> IngestResponse:
    """Endpoint para ingestão de documentos."""
    body = payload or IngestRequest()

    # Validações de negócio
    if body.chunk_overlap >= body.chunk_size:
        raise HTTPException(status_code=400, detail="chunk_overlap must be lower than chunk_size")

    if not settings.openai_api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured")

    # Criar DTO
    request_dto = IngestRequestDTO(
        docs_dir=Path(body.docs_dir) if body.docs_dir else settings.docs_dir,
        chunk_size=body.chunk_size or settings.chunk_size,
        chunk_overlap=body.chunk_overlap if body.chunk_overlap is not None else settings.chunk_overlap,
        embedding_model=body.embedding_model or settings.embedding_model,
    )

    # Executar caso de uso
    try:
        ingest_uc, _ = _create_use_cases()
        result: IngestResultDTO = ingest_uc.execute(request_dto)

        return IngestResponse(
            documents_count=result.documents_count,
            chunks_count=result.chunks_count,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Endpoint para health check."""
    try:
        _, health_uc = _create_use_cases()
        status = health_uc.execute()

        return HealthResponse(
            api_status=status.api_status,
            vector_store_status=status.vector_store_status,
            indexed_documents_count=status.indexed_documents_count,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")
