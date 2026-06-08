from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """DTO para requisição de consulta RAG."""
    
    query: str = Field(..., min_length=1, description="Texto da consulta")
    top_k: int = Field(default=5, ge=1, le=20, description="Número máximo de resultados")
    threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Limiar de similaridade")


class QueryResult(BaseModel):
    """DTO para resultado de uma consulta RAG."""
    
    chunk_id: str = Field(..., description="ID do chunk")
    document_id: str = Field(..., description="ID do documento")
    content: str = Field(..., description="Conteúdo do chunk")
    score: float = Field(..., description="Score de similaridade")
    metadata: dict = Field(default_factory=dict, description="Metadados adicionais")


class QueryResponse(BaseModel):
    """DTO para resposta da consulta RAG."""
    
    query: str = Field(..., description="Consulta original")
    results: List[QueryResult] = Field(..., description="Resultados encontrados")
    total_results: int = Field(..., description="Total de resultados retornados")
    processing_time_ms: float = Field(..., description="Tempo de processamento em ms")
