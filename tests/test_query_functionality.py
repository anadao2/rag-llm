from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, Mock

from app.application.dto.query_dto import QueryRequest, QueryResponse, QueryResult
from app.application.use_cases.query_documents import QueryDocumentsUseCase
from app.domain.entities.chunk import Chunk
from app.domain.repositories.chunk_repository import ChunkRepository
from app.domain.services.embedding_service import EmbeddingService
from app.domain.value_objects.chunk_id import ChunkId
from app.domain.value_objects.document_id import DocumentId
from app.domain.value_objects.embedding import Embedding


class TestQueryRequest:
    """Testes para QueryRequest DTO seguindo princípios SOLID."""
    
    def test_query_request_valid(self):
        """Testa criação de QueryRequest válido."""
        request = QueryRequest(query="test query", top_k=5, threshold=0.7)
        assert request.query == "test query"
        assert request.top_k == 5
        assert request.threshold == 0.7
    
    def test_query_request_defaults(self):
        """Testa valores padrão do QueryRequest."""
        request = QueryRequest(query="test")
        assert request.top_k == 5
        assert request.threshold == 0.7
    
    def test_query_request_invalid_query(self):
        """Testa validação de query inválido."""
        with pytest.raises(ValueError):
            QueryRequest(query="")
    
    def test_query_request_invalid_top_k(self):
        """Testa validação de top_k inválido."""
        with pytest.raises(ValueError):
            QueryRequest(query="test", top_k=0)
    
    def test_query_request_invalid_threshold(self):
        """Testa validação de threshold inválido."""
        with pytest.raises(ValueError):
            QueryRequest(query="test", threshold=1.5)


class TestQueryResult:
    """Testes para QueryResult DTO."""
    
    def test_query_result_creation(self):
        """Testa criação de QueryResult."""
        result = QueryResult(
            chunk_id="chunk1",
            document_id="docdoc1",
            content="test content",
            score=0.8,
            metadata={"key": "value"}
        )
        assert result.chunk_id == "chunk1"
        assert result.document_id == "doc1"
        assert result.content == "test content"
        assert result.score == 0.8
        assert result.metadata == {"key": "value"}


class MockChunkRepository(ChunkRepository):
    """Mock de ChunkRepository para testes (Dependency Inversion)."""
    
    def __init__(self, chunks: list[Chunk] | None = None):
        self._chunks = chunks or []
    
    def save(self, chunk: Chunk) -> None:
        self._chunks.append(chunk)
    
    def save_batch(self, chunks: list[Chunk]) -> None:
        self._chunks.extend(chunks)
    
    def find_by_id(self, chunk_id: ChunkId) -> Chunk | None:
        for chunk in self._chunks:
            if chunk.chunk_id == chunk_id:
                return chunk
        return None
    
    def find_by_document_id(self, doc_id: DocumentId) -> list[Chunk]:
        return [chunk for chunk in self._chunks if chunk.document_id == doc_id]
    
    def search_similar(self, query_embedding: list[float], top_k: int = 5) -> list[Chunk]:
        return self._chunks[:top_k]
    
    def count(self) -> int:
        return len(self._chunks)


class MockEmbeddingService(EmbeddingService):
    """Mock de EmbeddingService para testes."""
    
    def __init__(self):
        self.embed_text_called = False
    
    async def embed_text(self, text: str) -> Embedding:
        self.embed_text_called = True
        return Embedding([0.1, 0.2, 0.3])
    
    async def embed_chunks(self, chunks: list[Chunk]) -> list[Chunk]:
        for chunk in chunks:
            chunk.embedding = Embedding([0.1, 0.2, 0.3])
        return chunks


class TestQueryDocumentsUseCase:
    """Testes para QueryDocumentsUseCase seguindo SOLID."""
    
    @pytest.fixture
    def mock_chunk_repository(self):
        """Fixture para mock de ChunkRepository."""
        chunk = Chunk(
            chunk_id=ChunkId("chunk1"),
            document_id=DocumentId("docdoc1"),
            content="test content",
            embedding=Embedding([0.1, 0.2, 0.3])
        )
        return MockChunkRepository([chunk])
    
    @pytest.fixture
    def mock_embedding_service(self):
        """Fixture para mock de EmbeddingService."""
        return MockEmbeddingService()
    
    @pytest.fixture
    def use_case(self, mock_chunk_repository, mock_embedding_service):
        """Fixture para QueryDocumentsUseCase."""
        return QueryDocumentsUseCase(
            chunk_repository=mock_chunk_repository,
            embedding_service=mock_embedding_service
        )
    
    @pytest.mark.asyncio
    async def test_execute_successful_query(self, use_case, mock_chunk_repository, mock_embedding_service):
        """Testa execução bem-sucedida de consulta."""
        request = QueryRequest(query="test query", top_k=5, threshold=0.7)
        
        response = await use_case.execute(request)
        
        assert isinstance(response, QueryResponse)
        assert response.query == "test query"
        assert len(response.results) == 1
        assert response.total_results == 1
        assert response.processing_time_ms > 0
        assert mock_embedding_service.embed_text_called
    
    @pytest.mark.asyncio
    async def test_execute_no_results_above_threshold(self, use_case, mock_chunk_repository, mock_embedding_service):
        """Testa consulta sem resultados acima do threshold."""
        request = QueryRequest(query="test query", threshold=0.9)
        
        response = await use_case.execute(request)
        
        assert response.total_results == 0
        assert len(response.results) == 0
    
    @pytest.mark.asyncio
    async def test_execute_empty_repository(self, mock_embedding_service):
        """Testa consulta em repositório vazio."""
        empty_repo = MockChunkRepository([])
        use_case = QueryDocumentsUseCase(empty_repo, mock_embedding_service)
        
        request = QueryRequest(query="test query")
        response = await use_case.execute(request)
        
        assert response.total_results == 0
        assert len(response.results) == 0
    
    @pytest.mark.asyncio
    async def test_execute_top_k_limit(self, mock_embedding_service):
        """Testa limite de top_k resultados."""
        chunks = [
            Chunk(
                chunk_id=ChunkId(f"chunk{i}"),
                document_id=DocumentId("theodoc1"),
                content=f"content {i}",
                embedding=Embedding([0.1, 0.2, 0.3])
            )
            for i in range(10)
        ]
        repo = MockChunkRepository(chunks)
        use_case = QueryDocumentsUseCase(repo, mock_embedding_service)
        
        request = QueryRequest(query="test query", top_k=3)
        response = await use_case.execute(request)
        
        assert len(response.results) <= 3


class TestQueryIntegration:
    """Testes de integração para funcionalidade de consulta."""
    
    @pytest.mark.asyncio
    async def test_query_end_to_end(self):
        """Teste end-to-end da funcionalidade de consulta."""
        # Setup
        mock_repo = MockChunkRepository()
        mock_service = MockEmbeddingService()
        use_case = QueryDocumentsUseCase(mock_repo, mock_service)
        
        # Test
        request = QueryRequest(query="integration test")
        response = await use_case.execute(request)
        
        # Assert
        assert response.query == "integration test"
        assert isinstance(response.results, list)
        assert isinstance(response.processing_time_ms, float)


if __name__ == "__main__":
    pytest.main([__file__])
