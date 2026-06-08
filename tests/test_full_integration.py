from __future__ import annotations

import pytest
import tempfile
import asyncio
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from app.main import app
from app.application.use_cases.ingest_documents import IngestDocumentsUseCase
from app.application.use_cases.query_documents import QueryDocumentsUseCase
from app.application.dto.ingest_dto import IngestRequest
from app.application.dto.query_dto import QueryRequest
from app.infrastructure.external.openai_embedder import OpenAIEmbedder
from app.infrastructure.persistence.faiss_chunk_repository import FaissChunkRepository
from app.infrastructure.persistence.json_document_repository import JsonDocumentRepository
from app.domain.services.chunking_service import ChunkingService
from app.domain.services.embedding_service import EmbeddingService


class TestFullAPIIntegration:
    """Testes de integração completa da API RAG."""
    
    @pytest.fixture
    def client(self):
        """Fixture para cliente de teste FastAPI."""
        return TestClient(app)
    
    @pytest.fixture
    def temp_dir(self):
        """Fixture para diretório temporário."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def test_docs_dir(self, temp_dir):
        """Fixture para documentos de teste."""
        docs_dir = temp_dir / "test_docs"
        docs_dir.mkdir()
        
        (docs_dir / "ai.txt").write_text("""
        Artificial Intelligence (AI) is a branch of computer science that aims to create intelligent machines 
        that can perform tasks that typically require human intelligence. Machine learning is a subset of AI 
        that focuses on algorithms that can learn from data.
        """)
        
        (docs_dir / "python.txt").write_text("""
        Python is a high-level programming language that is widely used in AI and machine learning.
        Libraries like TensorFlow, PyTorch, and scikit-learn make Python popular for data science.
        """)
        
        return docs_dir
    
    @pytest.fixture
    def mock_faiss_dir(self, temp_dir):
        """Fixture para diretório FAISS mock."""
        faiss_dir = temp_dir / "faiss"
        faiss_dir.mkdir()
        return faiss_dir
    
    def test_full_rag_workflow_api(self, client, test_docs_dir, mock_faiss_dir):
        """Teste completo do workflow RAG via API."""
        
        with patch('app.api.routes.ingest.settings') as mock_ingest_settings:
            with patch('app.api.routes.query.settings') as mock_query_settings:
                # Configurar mocks
                mock_ingest_settings.openai_api_key = "test-key"
                mock_ingest_settings.docs_dir = str(test_docs_dir)
                mock_ingest_settings.chunk_size = 100
                mock_ingest_settings.chunk_overlap = 20
                mock_ingest_settings.embedding_model = "text-embedding-3-small"
                mock_ingest_settings.faiss_dir = str(mock_faiss_dir)
                
                mock_query_settings.openai_api_key = "test-key"
                mock_query_settings.faiss_dir = str(mock_faiss_dir)
                mock_query_settings.embedding_model = "text-embedding-3-small"
                
                # Mock do OpenAIEmbedder
                with patch('app.api.routes.ingest.OpenAIEmbedder') as mock_ingest_embedder:
                    with patch('app.api.routes.query.OpenAIEmbedder') as mock_query_embedder:
                        
                        # Configurar mocks de embedding
                        mock_ingest_client = AsyncMock()
                        mock_ingest_client.embed.return_value = [[0.1, 0.2, 0.3] for _ in range(10)]
                        mock_ingest_embedder.return_value = mock_ingest_client
                        
                        mock_query_client = AsyncMock()
                        mock_query_client.embed.return_value = [[0.1, 0.2, 0.3]]
                        mock_query_embedder.return_value = mock_query_client
                        
                        # 1. Testar health endpoint
                        health_response = client.get("/health")
                        assert health_response.status_code == 200
                        health_data = health_response.json()
                        assert health_data["api_status"] == "ok"
                        
                        # 2. Ingerir documentos
                        ingest_response = client.post("/ingest", json={
                            "docs_dir": str(test_docs_dir),
                            "chunk_size": 100,
                            "chunk_overlap": 20,
                            "embedding_model": "text-embedding-3-small"
                        })
                        
                        assert ingest_response.status_code == 200
                        ingest_data = ingest_response.json()
                        assert ingest_data["documents_count"] == 2
                        assert ingest_data["chunks_count"] > 0
                        
                        # 3. Consultar documentos
                        query_response = client.post("/query", json={
                            "query": "What is Python programming?",
                            "top_k": 3,
                            "threshold": 0.5
                        })
                        
                        assert query_response.status_code == 200
                        query_data = query_response.json()
                        assert query_data["query"] == "What is Python programming?"
                        assert isinstance(query_data["results"], list)
                        assert query_data["total_results"] >= 0
                        assert query_data["processing_time_ms"] > 0
    
    def test_api_error_handling(self, client):
        """Testa tratamento de erros na API."""
        
        with patch('app.api.routes.query.settings') as mock_settings:
            mock_settings.openai_api_key = None  # API key não configurada
            
            response = client.post("/query", json={"query": "test"})
            assert response.status_code == 500
            assert "OPENAI_API_KEY is not configured" in response.json()["detail"]
    
    def test_api_validation_errors(self, client):
        """Testa erros de validação na API."""
        
        # Query vazia
        response = client.post("/query", json={"query": ""})
        assert response.status_code == 422
        
        # top_k inválido
        response = client.post("/query", json={
            "query": "test",
            "top_k": 0
        })
        assert response.status_code == 422
        
        # threshold inválido
        response = client.post("/query", json={
            "query": "test",
            "threshold": 1.5
        })
        assert response.status_code == 422
    
    def test_concurrent_api_requests(self, client, test_docs_dir, mock_faiss_dir):
        """Testa requisições concorrentes na API."""
        
        with patch('app.api.routes.query.settings') as mock_settings:
            mock_settings.openai_api_key = "test-key"
            mock_settings.faiss_dir = str(mock_faiss_dir)
            mock_settings.embedding_model = "text-embedding-3-small"
            
            with patch('app.api.routes.query.OpenAIEmbedder') as mock_embedder:
                mock_client = AsyncMock()
                mock_client.embed.return_value = [[0.1, 0.2, 0.3]]
                mock_embedder.return_value = mock_client
                
                # Enviar múltiplas requisições concorrentes
                import threading
                import time
                
                results = []
                
                def make_request(query_id):
                    response = client.post("/query", json={
                        "query": f"Test query {query_id}",
                        "top_k": 2
                    })
                    results.append(response.status_code)
                
                # Criar 10 threads concorrentes
                threads = []
                start_time = time.time()
                
                for i in range(10):
                    thread = threading.Thread(target=make_request, args=(i,))
                    threads.append(thread)
                    thread.start()
                
                # Esperar todas as threads completarem
                for thread in threads:
                    thread.join()
                
                end_time = time.time()
                
                # Verificar resultados
                assert len(results) == 10
                assert all(status == 200 for status in results)
                assert end_time - start_time < 5.0  # Deve completar em menos de 5 segundos
    
    def test_api_response_format(self, client, mock_faiss_dir):
        """Testa formato da resposta da API."""
        
        with patch('app.api.routes.query.settings') as mock_settings:
            mock_settings.openai_api_key = "test-key"
            mock_settings.faiss_dir = str(mock_faiss_dir)
            mock_settings.embedding_model = "text-embedding-3-small"
            
            with patch('app.api.routes.query.OpenAIEmbedder') as mock_embedder:
                mock_client = AsyncMock()
                mock_client.embed.return_value = [[0.1, 0.2, 0.3]]
                mock_embedder.return_value = mock_client
                
                response = client.post("/query", json={
                    "query": "test query",
                    "top_k": 2,
                    "threshold": 0.5
                })
                
                assert response.status_code == 200
                data = response.json()
                
                # Verificar estrutura da resposta
                required_fields = ["query", "results", "total_results", "processing_time_ms"]
                for field in required_fields:
                    assert field in data, f"Missing field: {field}"
                
                # Verificar tipos
                assert isinstance(data["query"], str)
                assert isinstance(data["results"], list)
                assert isinstance(data["total_results"], int)
                assert isinstance(data["processing_time_ms"], (int, float))
                
                # Verificar estrutura dos resultados (se houver)
                for result in data["results"]:
                    result_fields = ["chunk_id", "document_id", "content", "score", "metadata"]
                    for field in result_fields:
                        assert field in result, f"Missing result field: {field}"
                    
                    assert isinstance(result["chunk_id"], str)
                    assert isinstance(result["document_id"], str)
                    assert isinstance(result["content"], str)
                    assert isinstance(result["score"], (int, float))
                    assert isinstance(result["metadata"], dict)
    
    def test_api_performance_metrics(self, client, mock_faiss_dir):
        """Testa métricas de performance da API."""
        
        with patch('app.api.routes.query.settings') as mock_settings:
            mock_settings.openai_api_key = "test-key"
            mock_settings.faiss_dir = str(mock_faiss_dir)
            mock_settings.embedding_model = "text-embedding-3-small"
            
            with patch('app.api.routes.query.OpenAIEmbedder') as mock_embedder:
                mock_client = AsyncMock()
                mock_client.embed.return_value = [[0.1, 0.2, 0.3]]
                mock_embedder.return_value = mock_client
                
                # Medir tempo de resposta
                import time
                
                queries = [
                    "artificial intelligence",
                    "machine learning algorithms", 
                    "python programming",
                    "data science",
                    "neural networks"
                ]
                
                response_times = []
                
                for query in queries:
                    start_time = time.time()
                    response = client.post("/query", json={"query": query})
                    end_time = time.time()
                    
                    assert response.status_code == 200
                    response_times.append(end_time - start_time)
                    
                    data = response.json()
                    assert data["processing_time_ms"] > 0
                
                # Verificar métricas
                avg_response_time = sum(response_times) / len(response_times)
                assert avg_response_time < 1.0  # Média menos que 1 segundo
                
                max_response_time = max(response_times)
                assert max_response_time < 2.0  # Máximo menos que 2 segundos


class TestAPIEdgeCases:
    """Testes de casos extremos para a API."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_empty_database_queries(self, client):
        """Testa consultas em base de dados vazia."""
        
        with patch('app.api.routes.query.settings') as mock_settings:
            mock_settings.openai_api_key = "test-key"
            mock_settings.faiss_dir = "/nonexistent/path"
            mock_settings.embedding_model = "text-embedding-3-small"
            
            with patch('app.api.routes.query.OpenAIEmbedder') as mock_embedder:
                mock_client = AsyncMock()
                mock_client.embed.return_value = [[0.1, 0.2, 0.3]]
                mock_embedder.return_value = mock_client
                
                response = client.post("/query", json={"query": "test query"})
                assert response.status_code == 200
                
                data = response.json()
                assert data["total_results"] == 0
                assert len(data["results"]) == 0
    
    def test_malformed_requests(self, client):
        """Testa requisições malformadas."""
        
        # JSON inválido
        response = client.post("/query", data="invalid json")
        assert response.status_code == 422
        
        # Campo ausente
        response = client.post("/query", json={"top_k": 5})
        assert response.status_code == 422
        
        # Tipos incorretos
        response = client.post("/query", json={
            "query": 123,  # Deveria ser string
            "top_k": "5"   # Deveria ser int
        })
        assert response.status_code == 422
    
    def test_large_query_handling(self, client, mock_faiss_dir):
        """Testa handling de queries muito grandes."""
        
        with patch('app.api.routes.query.settings') as mock_settings:
            mock_settings.openai_api_key = "test-key"
            mock_settings.faiss_dir = str(mock_faiss_dir)
            mock_settings.embedding_model = "text-embedding-3-small"
            
            with patch('app.api.routes.query.OpenAIEmbedder') as mock_embedder:
                mock_client = AsyncMock()
                mock_client.embed.return_value = [[0.1, 0.2, 0.3]]
                mock_embedder.return_value = mock_client
                
                # Query muito longa
                long_query = "test " * 1000  # ~5000 caracteres
                
                response = client.post("/query", json={"query": long_query})
                assert response.status_code == 200
                
                data = response.json()
                assert data["query"] == long_query
                assert data["processing_time_ms"] > 0


if __name__ == "__main__":
    pytest.main([__file__])
