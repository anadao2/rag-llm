from __future__ import annotations

from fastapi import APIRouter, HTTPException, Depends

from app.application.dto.query_dto import QueryRequest, QueryResponse
from app.application.use_cases.query_documents import QueryDocumentsUseCase
from app.core.config import settings
from app.domain.services.embedding_service import EmbeddingService
from app.infrastructure.external.openai_embedder import OpenAIEmbedder
from app.infrastructure.persistence.faiss_chunk_repository import FaissChunkRepository

router = APIRouter(tags=["query"])


def get_query_use_case() -> QueryDocumentsUseCase:
    """
    Factory function para criar o use case de consulta.
    Segue o princípio de Inversão de Dependência (DIP).
    """
    # Criar dependências
    embed_client = OpenAIEmbedder(api_key=settings.openai_api_key)
    embedding_service = EmbeddingService(client=embed_client, model=settings.embedding_model)
    chunk_repository = FaissChunkRepository(settings.faiss_dir)
    
    return QueryDocumentsUseCase(
        chunk_repository=chunk_repository,
        embedding_service=embedding_service
    )


@router.post("/query", response_model=QueryResponse)
async def query_documents(
    request: QueryRequest,
    use_case: QueryDocumentsUseCase = Depends(get_query_use_case)
) -> QueryResponse:
    """
    Endpoint para consultar documentos usando RAG.
    
    Args:
        request: Requisição de consulta RAG
        use_case: Use case injetado de consulta
        
    Returns:
        QueryResponse: Resultados da consulta
        
    Raises:
        HTTPException: Se a API key não estiver configurada
    """
    if not settings.openai_api_key:
        raise HTTPException(
            status_code=500, 
            detail="OPENAI_API_KEY is not configured"
        )
    
    try:
        return await use_case.execute(request)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )
