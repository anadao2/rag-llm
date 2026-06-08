from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock

from app.main import app
from app.application.dto.query_dto import QueryRequest, QueryResponse, QueryResult


class TestQueryAPI:
    """Testes para API de consulta seguindo princípios SOLID."""
    
    @pytest.fixture
    def client(self):
        """Fixture para cliente de teste FastAPI."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_query_response(self):
        """Fixture para resposta mock de consulta."""
        return QueryResponse(
            query="test query",
            results=[
                QueryResult(
                    chunk_id="chunk1",
                    document_id="theodoc1",
                    content="test content",
                    score=0.8,
                    metadata={}
                )
            ],
            total_results=1,
            processing_time_ms=150.5
        )
    
    def test_query_endpoint_success(self, client, mock_query_response):
        """Testa endpoint de consulta com sucesso."""
        with patch('app.api.routes.query.get_query_use_case') as mock_get_use_case:
            mock_use_case = AsyncMock()
            mock_use_case.execute.return_value = mock_query_response
            mock_get_use_case.return_value = mock_use_case
            
            response = client.post("/query", json={
                "query": "test query",
                "top_k": 5,
                "threshold": 0.7
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["query"] == "test query"
            assert len(data["results"]) == 1
            assert data["total_results"] == 1
            assert data["processing_time_ms"] == 150.5
    
    def test_query_endpoint_missing_api_key(self, client):
        """Testa endpoint quando API key não está configurada."""
        with patch('app.api.routes.query.settings') as mock_settings:
            mock_settings.openai_api_key = None
            
            response = client.post("/query", json={"query": "test"})
            
            assert response.status_code == 500
            assert "OPENAI_API_KEY is not configured" in response.json()["detail"]
    
    def test_query_endpoint_invalid_request(self, client):
        """Testa endpoint com requisição inválida."""
        response = client.post("/query", json={"query": ""})
        
        assert response.status_code == 422  # Validation error
    
    def test_query_endpoint_use_case_exception(self, client):
        """Testa endpoint quando use case lança exceção."""
        with patch('app.api.routes.query.get_query_use_case') as mock_get_use_case:
            mock_use_case = AsyncMock()
            mock_use_case.execute.side_effect = Exception("Test error")
            mock_get_use_case.return_value = mock_use_case
            
            response = client.post("/query", json={"query": "test"})
            
            assert response.status_code == 500
            assert "Error processing query" in response.json()["detail"]
    
    def test_query_endpoint_default_values(self, client, mock_query_response):
        """Testa endpoint com valores padrão."""
        with patch('app.api.routes.query.get_query_use_case') as mock_get_use_case:
            mock_use_case = AsyncMock()
            mock_use_case.execute.return_value = mock_query_response
            mock_get_use_case.return_value = mock_use_case
            
            response = client.post("/query", json={"query": "test"})
            
            assert response.status_code == 200
            # Verifica se o use case foi chamado com valores padrão
            mock_use_case.execute.assert_called_once()
            call_args = mock_use_case.execute.call_args[0][0]
            assert isinstance(call_args, QueryRequest)
            assert call_args.query == "test"
            assert call_args.top_k == 5
            assert call_args.threshold == 0.7
    
    def test_query_endpoint_validation_top_k(self, client):
        """Testa validação do parâmetro top_k."""
        response = client.post("/query", json={
            "query": "test",
            "top_k": 0  # Inválido
        })
        
        assert response.status_code == 422
    
    def test_query_endpoint_validation_threshold(self, client):
        """Testa validação do parâmetro threshold."""
        response = client.post("/query", json={
            "query": "test",
            "threshold": 1.5  # Inválido
        })
        
        assert response.status_code == 422
    
    def test_query_endpoint_max_top_k(self, client, mock_query_response):
        """Testa endpoint com valor máximo de top_k."""
        with patch('app.api.routes.query.get_query_use_case') as mock_get_use_case:
            mock_use_case = AsyncMock()
            mock_use_case.execute.return_value = mock_query_response
            mock_get_use_case.return_value = mock_use_case
            
            response = client.post("/query", json={
                "query": "test",
                "top_k": 20  # Valor máximo
            })
            
            assert response.status_code == 200
    
    def test_query_endpoint_exceeds_max_top_k(self, client):
        """Testa endpoint com top_k acima do máximo."""
        response = client.post("/query", json={
            "query": "test",
            "top_k": 21  # Acima do máximo
        })
        
        assert response.status_code == 422


class TestQueryAPIDependencyInjection:
    """Testes para injeção de dependências na API de consulta."""
    
    def test_get_query_use_case_dependency_injection(self):
        """Testa se a injeção de dependência funciona corretamente."""
        from app.api.routes.query import get_query_use_case
        
        with patch('app.api.routes.query.settings') as mock_settings:
            mock_settings.openai_api_key = "test-key"
            mock_settings.faiss_dir = "/test/path"
            mock_settings.embedding_model = "text-embedding-3-small"
            
            with patch('app.api.routes.query.OpenAIEmbedder') as mock_client:
                with patch('app.api.routes.query.EmbeddingService') as mock_service:
                    with patch('app.api.routes.query.FaissChunkRepository') as mock_repo:
                        use_case = get_query_use_case()
                        
                        assert use_case is not None
                        mock_client.assert_called_once_with(api_key="test-key")
                        mock_service.assert_called_once()
                        mock_repo.assert_called_once_with("/test/path")


if __name__ == "__main__":
    pytest.main([__file__])
