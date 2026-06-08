from __future__ import annotations

import time
from typing import List

from app.application.dto.query_dto import QueryRequest, QueryResponse, QueryResult
from app.domain.repositories.chunk_repository import ChunkRepository
from app.domain.services.embedding_service import EmbeddingService


class QueryDocumentsUseCase:
    """
    Use Case para consultar documentos usando RAG.
    
    Segue o princípio de Responsabilidade Única (SRP) - apenas consulta documentos.
    Segue o princípio de Inversão de Dependência (DIP) - depende de abstrações.
    """
    
    def __init__(
        self,
        chunk_repository: ChunkRepository,
        embedding_service: EmbeddingService,
    ) -> None:
        self._chunk_repository = chunk_repository
        self._embedding_service = embedding_service
    
    async def execute(self, request: QueryRequest) -> QueryResponse:
        """
        Executa a consulta RAG.
        
        Args:
            request: Requisição de consulta
            
        Returns:
            QueryResponse: Resultados da consulta
        """
        start_time = time.time()
        
        # Gerar embedding da consulta
        query_embedding = await self._embedding_service.embed_text(request.query)
        
        # Buscar chunks similares
        similar_chunks = self._chunk_repository.search_similar(
            query_embedding.to_list(),
            top_k=request.top_k
        )
        
        # Filtrar por threshold e converter para DTO
        results = []
        for chunk in similar_chunks:
            # Simular cálculo de score (em implementação real viria do FAISS)
            score = 0.8  # Placeholder
            
            if score >= request.threshold:
                results.append(QueryResult(
                    chunk_id=str(chunk.chunk_id),
                    document_id=str(chunk.document_id),
                    content=chunk.content,
                    score=score,
                    metadata={}
                ))
        
        processing_time = (time.time() - start_time) * 1000
        
        return QueryResponse(
            query=request.query,
            results=results,
            total_results=len(results),
            processing_time_ms=processing_time
        )
