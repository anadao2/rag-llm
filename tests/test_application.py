"""Testes unitários para o Application Layer."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import List
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.application.dto.ingest_dto import IngestRequestDTO, IngestResultDTO
from app.application.dto.health_dto import HealthStatusDTO
from app.application.use_cases.ingest_documents import IngestDocumentsUseCase
from app.application.use_cases.get_health_status import GetHealthStatusUseCase
from app.domain.entities.chunk import Chunk
from app.domain.entities.document import Document
from app.domain.repositories.document_repository import DocumentRepository
from app.domain.repositories.chunk_repository import ChunkRepository
from app.domain.services.embedding_service import EmbeddingClient
from app.domain.value_objects.document_id import DocumentId


def test_ingest_request_dto():
    """Testa criação de DTO."""
    dto = IngestRequestDTO(
        docs_dir=Path("/docs"),
        chunk_size=500,
        chunk_overlap=50,
        embedding_model="text-embedding-3-small",
    )
    assert dto.chunk_size == 500
    assert dto.chunk_overlap == 50
    print("[OK] IngestRequestDTO creation works")


def test_health_status_dto():
    """Testa criação de HealthStatusDTO."""
    dto = HealthStatusDTO(
        api_status="ok",
        vector_store_status="ready",
        indexed_documents_count=5,
        indexed_chunks_count=25,
    )
    assert dto.api_status == "ok"
    assert dto.indexed_documents_count == 5
    print("[OK] HealthStatusDTO creation works")


def test_use_case_with_mocks():
    """Testa use case com mocks."""
    # Criar mocks
    mock_doc_repo = Mock(spec=DocumentRepository)
    mock_chunk_repo = Mock(spec=ChunkRepository)
    mock_embedder = Mock(spec=EmbeddingClient)
    
    # Configurar comportamento
    mock_doc_repo.save_batch = Mock()
    mock_chunk_repo.save_batch = Mock()
    mock_chunk_repo.is_ready = Mock(return_value=True)
    mock_doc_repo.count = Mock(return_value=0)
    mock_chunk_repo.count = Mock(return_value=0)
    mock_embedder.embed = Mock(return_value=[[0.1, 0.2, 0.3]])
    
    # Criar use case
    use_case = IngestDocumentsUseCase(
        document_repo=mock_doc_repo,
        chunk_repo=mock_chunk_repo,
        embedding_client=mock_embedder,
    )
    
    # Verificar que use case foi criado
    assert use_case is not None
    assert use_case.document_repo == mock_doc_repo
    print("[OK] IngestDocumentsUseCase with mocks works")


def test_health_use_case_with_mocks():
    """Testa health use case com mocks."""
    mock_doc_repo = Mock(spec=DocumentRepository)
    mock_chunk_repo = Mock(spec=ChunkRepository)
    
    mock_doc_repo.count = Mock(return_value=5)
    mock_chunk_repo.count = Mock(return_value=25)
    mock_chunk_repo.is_ready = Mock(return_value=True)
    
    use_case = GetHealthStatusUseCase(
        document_repo=mock_doc_repo,
        chunk_repo=mock_chunk_repo,
    )
    
    result = use_case.execute()
    
    assert result.api_status == "ok"
    assert result.vector_store_status == "ok"
    assert result.indexed_documents_count == 5
    assert result.indexed_chunks_count == 25
    print("[OK] GetHealthStatusUseCase with mocks works")


def run_all_tests():
    """Roda todos os testes da application layer."""
    print("\n=== Application Layer Tests ===")
    test_ingest_request_dto()
    test_health_status_dto()
    test_use_case_with_mocks()
    test_health_use_case_with_mocks()
    print("\n[PASS] All Application tests passed!")


if __name__ == "__main__":
    run_all_tests()

