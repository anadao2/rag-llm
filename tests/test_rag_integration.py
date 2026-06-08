from __future__ import annotations

import pytest
import tempfile
import asyncio
from pathlib import Path
from unittest.mock import patch, AsyncMock

from app.application.use_cases.ingest_documents import IngestDocumentsUseCase
from app.application.use_cases.query_documents import QueryDocumentsUseCase
from app.application.dto.ingest_dto import IngestRequest
from app.application.dto.query_dto import QueryRequest
from app.domain.factories.service_factory import ServiceFactory
from app.infrastructure.external.openai_embedder import OpenAIEmbedder
from app.infrastructure.persistence.faiss_chunk_repository import FaissChunkRepository
from app.infrastructure.persistence.json_document_repository import JsonDocumentRepository
from app.domain.services.chunking_service import ChunkingService


class TestRAGIntegration:
    """Testes de integração completa do sistema RAG seguindo SOLID."""
    
    @pytest.fixture
    def temp_dir(self):
        """Fixture para diretório temporário."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def docs_dir(self, temp_dir):
        """Fixture para diretório de documentos de teste."""
        docs_dir = temp_dir / "docs"
        docs_dir.mkdir()
        
        # Criar documentos de teste
        (docs_dir / "doc1.txt").write_text("Python is a programming language. Python is widely used for data science and machine learning.")
        (docs_dir / "theodoc2.txt").write_text("Machine learning involves training models on data. Deep learning is a subset of machine learning.")
        
        return docs_dir
    
    @pytest.fixture
    def faiss_dir(self, temp_dir):
        """Fixture para diretório FAISS."""
        faiss_dir = temp_dir / "faiss"
        faiss_dir.mkdir()
        return faiss_dir
    
    @pytest.fixture
    def mock_embedding_client(self):
        """Mock para cliente de embedding."""
        client = AsyncMock(spec=OpenAIEmbedder)
        
        def mock_embed(texts: list[str]) -> list[list[float]]:
            # Simular embedding baseado no conteúdo
            results = []
            for text in texts:
                if "python" in text.lower():
                    results.append([0.8, 0.1, 0.1])
                elif "machine learning" in text.lower():
                    results.append([0.1, 0.8, 0.1])
                elif "data" in text.lower():
                    results.append([0.1, 0.1, 0.8])
                else:
                    results.append([0.3, 0.3, 0.4])
            return results
        
        client.embed.side_effect = mock_embed
        return client
    
    @pytest.fixture
    def chunking_service(self):
        """Fixture para serviço de chunking."""
        return ChunkingService(chunk_size=50, overlap=10)
    
    @pytest.fixture
    def document_repository(self, temp_dir):
        """Fixture para repositório de documentos."""
        return JsonDocumentRepository(temp_dir / "documents.json")
    
    @pytest.fixture
    def chunk_repository(self, faiss_dir):
        """Fixture para repositório de chunks."""
        return FaissChunkRepository(faiss_dir)
    
    @pytest.fixture
    def embedding_service(self, mock_embedding_client):
        """Fixture para serviço de embedding."""
        return ServiceFactory.create_embedding_service(mock_embedding_client)
    
    @pytest.fixture
    def ingest_use_case(self, document_repository, chunk_repository, chunking_service, embedding_service):
        """Fixture para use case de ingestão."""
        return IngestDocumentsUseCase(
            document_repository=document_repository,
            chunk_repository=chunk_repository,
            chunking_service=chunking_service,
            embedding_service=embedding_service
        )
    
    @pytest.fixture
    def query_use_case(self, chunk_repository, embedding_service):
        """Fixture para use case de consulta."""
        return QueryDocumentsUseCase(
            chunk_repository=chunk_repository,
            embedding_service=embedding_service
        )
    
    @pytest.mark.asyncio
    async def test_rag_complete_workflow(
        self,
        docs_dir,
        ingest_use_case,
        query_use_case
    ):
        """Teste completo do fluxo RAG: ingestão -> consulta."""
        
        # 1. Ingerir documentos
        ingest_request = IngestRequest(
            docs_dir=str(docs_dir),
            chunk_size=50,
            chunk_overlap=10,
            embedding_model="text-embedding-3-small"
        )
        
        ingest_response = await ingest_use_case.execute(ingest_request)
        
        assert ingest_response.documents_count == 2
        assert ingest_response.chunks_count > 0
        
        # 2. Consultar sobre Python
        python_query = QueryRequest(
            query="Tell me about Python programming",
            top_k=3,
            threshold=0.5
        )
        
        python_response = await query_use_case.execute(python_query)
        
        assert python_response.query == "Tell me about Python programming"
        assert python_response.total_results > 0
        assert python_response.processing_time_ms > 0
        
        # Verificar se resultados contêm conteúdo relevante
        python_contents = [result.content.lower() for result in python_response.results]
        assert any("python" in content for content in python_contents)
        
        # 3. Consultar sobre Machine Learning
        ml_query = QueryRequest(
            query="What is machine learning?",
            top_k=2,
            threshold=0.5
        )
        
        ml_response = await query_use_case.execute(ml_query)
        
        assert ml_response.query == "What is machine learning?"
        assert ml_response.total_results > 0
        
        # Verificar se resultados contêm conteúdo relevante
        ml_contents = [result.content.lower() for result in ml_response.results]
        assert any("machine learning" in content for content in ml_contents)
    
    @pytest.mark.asyncio
    async def test_rag_query_empty_database(self, query_use_case):
        """Testa consulta em base de dados vazia."""
        query_request = QueryRequest(query="test query")
        
        response = await query_use_case.execute(query_request)
        
        assert response.total_results == 0
        assert len(response.results) == 0
        assert response.processing_time_ms > 0
    
    @pytest.mark.asyncio
    async def test_rag_query_high_threshold(
        self,
        docs_dir,
        ingest_use_case,
        query_use_case
    ):
        """Testa consulta com threshold alto."""
        # Ingerir documentos primeiro
        ingest_request = IngestRequest(docs_dir=str(docs_dir))
        await ingest_use_case.execute(ingest_request)
        
        # Consultar com threshold muito alto
        query_request = QueryRequest(
            query="test query",
            threshold=0.99  # Threshold muito alto
        )
        
        response = await query_use_case.execute(query_request)
        
        # Não deve retornar resultados com threshold tão alto
        assert response.total_results == 0
    
    @pytest.mark.asyncio
    async def test_rag_performance_metrics(
        self,
        docs_dir,
        ingest_use_case,
        query_use_case
    ):
        """Testa métricas de performance do sistema RAG."""
        # Ingerir documentos
        ingest_request = IngestRequest(docs_dir=str(docs_dir))
        ingest_response = await ingest_use_case.execute(ingest_request)
        
        # Medir tempo de múltiplas consultas
        queries = [
            "Python programming",
            "Machine learning concepts",
            "Data science applications"
        ]
        
        total_time = 0
        for query_text in queries:
            query_request = QueryRequest(query=query_text)
            response = await query_use_case.execute(query_request)
            total_time += response.processing_time_ms
            
            assert response.processing_time_ms < 1000  # Menos de 1 segundo por consulta
        
        avg_time = total_time / len(queries)
        assert avg_time < 500  # Média menos que 500ms
    
    @pytest.mark.asyncio
    async def test_rag_concurrent_queries(
        self,
        docs_dir,
        ingest_use_case,
        query_use_case
    ):
        """Testa consultas concorrentes."""
        # Ingerir documentos
        ingest_request = IngestRequest(docs_dir=str(docs_dir))
        await ingest_use_case.execute(ingest_request)
        
        # Criar múltiplas consultas concorrentes
        queries = [
            QueryRequest(query=f"Query {i}")
            for i in range(5)
        ]
        
        # Executar consultas concorrentemente
        tasks = [query_use_case.execute(query) for query in queries]
        responses = await asyncio.gather(*tasks)
        
        # Verificar se todas as consultas retornaram
        assert len(responses) == 5
        for response in responses:
            assert isinstance(response.total_results, int)
            assert response.processing_time_ms > 0


class TestRAGAdvancedScenarios:
    """Testes avançados para cenários complexos do sistema RAG."""
    
    @pytest.fixture
    def complex_docs_dir(self, temp_dir):
        """Fixture para documentos complexos de teste."""
        docs_dir = temp_dir / "complex_docs"
        docs_dir.mkdir()
        
        # Documentos com diferentes tamanhos e conteúdos
        (docs_dir / "short.txt").write_text("AI research.")
        (docs_dir / "medium_medium.txt").write_text("Artificial intelligence and machine learning are transforming how we process data and make decisions. Neural networks form the foundation of deep learning systems.")
        (docs_dir / "long.txt").write_text("""
        Natural Language Processing (NLP) is a subfield of artificial intelligence that focuses on the interaction between computers and human language. 
        It involves several tasks including text classification, named entity recognition, sentiment analysis, and machine translation.
        Modern NLP systems often use transformer architectures like BERT and GPT to achieve state-of-the-art results.
        These models are pre-trained on large corpora of text data and can be fine-tuned for specific tasks.
        """)
        (docs_dir / "technical.txt").write_text("Vector embeddings represent text as numerical vectors in high-dimensional space. Similar concepts have similar vector representations. Cosine similarity measures the angle between vectors.")
        
        return docs_dir
    
    @pytest.mark.asyncio
    async def test_rag_with_various_document_sizes(
        self,
        complex_docs_dir,
        ingest_use_case,
        query_use_case
    ):
        """Testa RAG com documentos de diferentes tamanhos."""
        # Ingerir documentos variados
        ingest_request = IngestRequest(
            docs_dir=str(complex_docs_dir),
            chunk_size=100,
            chunk_overlap=20
        )
        ingest_response = await ingest_use_case.execute(ingest_request)
        
        assert ingest_response.documents_count == 4
        assert ingest_response.chunks_count > 0
        
        # Testar consultas específicas
        queries_and_expected_keywords = [
            ("What is NLP?", ["natural language", "nlp", "language"]),
            ("Tell me about vector embeddings", ["vector", "embeddings", "similarity"]),
            ("AI and machine learning", ["artificial intelligence", "machine learning"]),
            ("Short content", ["ai research"])
        ]
        
        for query, expected_keywords in queries_and_expected_keywords:
            query_request = QueryRequest(query=query, top_k=3, threshold=0.5)
            response = await query_use_case.execute(query_request)
            
            assert response.total_results > 0, f"No results for query: {query}"
            
            # Verificar se pelo menos um resultado contém palavras-chave esperadas
            found_keyword = False
            for result in response.results:
                content_lower = result.content.lower()
                if any(keyword.lower() in content_lower for keyword in expected_keywords):
                    found_keyword = True
                    break
            
            assert found_keyword, f"No relevant content found for query: {query}"
    
    @pytest.mark.asyncio
    async def test_rag_multilingual_queries(
        self,
        docs_dir,
        ingest_use_case,
        query_use_case
    ):
        """Testa consultas em diferentes idiomas."""
        # Ingerir documentos
        ingest_request = IngestRequest(docs_dir=str(docs_dir))
        await ingest_use_case.execute(ingest_request)
        
        # Consultas em diferentes idiomas (simulado)
        multilingual_queries = [
            ("Python programming", "english"),
            ("programação Python", "portuguese"),
            ("Python programmation", "french")
        ]
        
        for query, language in multilingual_queries:
            query_request = QueryRequest(query=query, top_k=2)
            response = await query_use_case.execute(query_request)
            
            # Verificar que o sistema processa diferentes idiomas
            assert response.processing_time_ms > 0
            assert isinstance(response.total_results, int)
    
    @pytest.mark.asyncio
    async def test_rag_edge_case_queries(
        self,
        docs_dir,
        ingest_use_case,
        query_use_case
    ):
        """Testa consultas de borda e casos especiais."""
        await ingest_use_case.execute(IngestRequest(docs_dir=str(docs_dir)))
        
        edge_cases = [
            ("", "empty query"),  # Query vazia
            ("a" * 1000, "very long query"),  # Query muito longa
            ("!@#$%^&*()", "special characters"),  # Caracteres especiais
            ("   spaced   query   ", "extra spaces"),  # Espaços extras
            ("Mixed CASE Query", "case sensitivity"),  # Case sensitivity
        ]
        
        for query, description in edge_cases:
            if query:  # Pular query vazia pois validação do Pydantic vai bloquear
                query_request = QueryRequest(query=query, top_k=3)
                response = await query_use_case.execute(query_request)
                
                assert response.query == query
                assert response.processing_time_ms > 0
                assert isinstance(response.results, list)
    
    @pytest.mark.asyncio
    async def test_rag_different_chunk_sizes(
        self,
        docs_dir,
        ingest_use_case,
        query_use_case
    ):
        """Testa RAG com diferentes tamanhos de chunk."""
        chunk_sizes = [25, 50, 100, 200]
        
        for chunk_size in chunk_sizes:
            # Ingerir com chunk size específico
            ingest_request = IngestRequest(
                docs_dir=str(docs_dir),
                chunk_size=chunk_size,
                chunk_overlap=chunk_size // 5
            )
            ingest_response = await ingest_use_case.execute(ingest_request)
            
            # Consultar
            query_request = QueryRequest(query="Python machine learning", top_k=5)
            response = await query_use_case.execute(query_request)
            
            assert ingest_response.chunks_count > 0
            assert response.processing_time_ms > 0
            
            # Verificar que chunks menores geralmente produzem mais resultados
            if chunk_size < 100:
                assert ingest_response.chunks_count >= 2
    
    @pytest.mark.asyncio
    async def test_rag_threshold_variations(
        self,
        docs_dir,
        ingest_use_case,
        query_use_case
    ):
        """Testa comportamento com diferentes thresholds."""
        await ingest_use_case.execute(IngestRequest(docs_dir=str(docs_dir)))
        
        thresholds = [0.0, 0.3, 0.5, 0.7, 0.9]
        results_by_threshold = {}
        
        for threshold in thresholds:
            query_request = QueryRequest(
                query="Python programming",
                threshold=threshold,
                top_k=10
            )
            response = await query_use_case.execute(query_request)
            results_by_threshold[threshold] = response.total_results
        
        # Threshold mais alto deve produzir menos ou iguais resultados
        for i in range(len(thresholds) - 1):
            lower_threshold = thresholds[i]
            higher_threshold = thresholds[i + 1]
            
            assert results_by_threshold[lower_threshold] >= results_by_threshold[higher_threshold], \
                f"Threshold {lower_threshold} should have >= results than {higher_threshold}"
    
    @pytest.mark.asyncio
    async def test_rag_performance_under_load(
        self,
        docs_dir,
        ingest_use_case,
        query_use_case
    ):
        """Testa performance sob carga."""
        await ingest_use_case.execute(IngestRequest(docs_dir=str(docs_dir)))
        
        # Simular carga com múltiplas consultas simultâneas
        import time
        
        start_time = time.time()
        
        queries = [
            f"Test query {i}" for i in range(20)
        ]
        
        tasks = [
            query_use_case.execute(QueryRequest(query=query))
            for query in queries
        ]
        
        responses = await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Verificar métricas de performance
        assert len(responses) == 20
        assert total_time < 10.0  # Todas as consultas em menos de 10 segundos
        
        avg_time_per_query = total_time / 20
        assert avg_time_per_query < 0.5  # Média menos que 500ms por consulta
        
        # Verificar que todas as respostas são válidas
        for response in responses:
            assert response.processing_time_ms > 0
            assert isinstance(response.results, list)


class TestRAGDataIntegrity:
    """Testes para integridade de dados no sistema RAG."""
    
    @pytest.mark.asyncio
    async def test_rag_document_persistence(
        self,
        docs_dir,
        ingest_use_case,
        query_use_case,
        document_repository
    ):
        """Testa persistência de documentos entre sessões."""
        # Primeira ingestão
        ingest_request = IngestRequest(docs_dir=str(docs_dir))
        await ingest_use_case.execute(ingest_request)
        
        # Verificar documentos persistidos
        assert document_repository.count() > 0
        
        # Consultar
        query_request = QueryRequest(query="Python programming")
        response = await query_use_case.execute(query_request)
        
        assert response.total_results > 0
        
        # Simular nova sessão (recarregar repositórios)
        # Em implementação real, isso testaria carregamento do disco
        docs = document_repository.find_all()
        assert len(docs) > 0
    
    @pytest.mark.asyncio
    async def test_rag_chunk_metadata_integrity(
        self,
        docs_dir,
        ingest_use_case,
        query_use_case
    ):
        """Testa integridade de metadados dos chunks."""
        await ingest_use_case.execute(IngestRequest(docs_dir=str(docs_dir)))
        
        query_request = QueryRequest(query="machine learning", top_k=5)
        response = await query_use_case.execute(query_request)
        
        # Verificar integridade dos metadados nos resultados
        for result in response.results:
            assert result.chunk_id, "Chunk ID should not be empty"
            assert result.document_id, "Document ID should not be empty"
            assert result.content, "Content should not be empty"
            assert 0 <= result.score <= 1, "Score should be between 0 and 1"
            assert isinstance(result.metadata, dict), "Metadata should be a dictionary"
    
    @pytest.mark.asyncio
    async def test_rag_consistency_across_queries(
        self,
        docs_dir,
        ingest_use_case,
        query_use_case
    ):
        """Testa consistência dos resultados através de múltiplas consultas."""
        await ingest_use_case.execute(IngestRequest(docs_dir=str(docs_dir)))
        
        # Mesma consulta múltiplas vezes
        query_text = "Python programming language"
        results_sets = []
        
        for _ in range(3):
            query_request = QueryRequest(query=query_text, top_k=3)
            response = await query_use_case.execute(query_request)
            results_sets.append([r.chunk_id for r in response.results])
        
        # Resultados devem ser consistentes (mesma ordem e conteúdo)
        for i in range(1, len(results_sets)):
            assert results_sets[0] == results_sets[i], \
                "Query results should be consistent across multiple executions"


class TestRAGErrorHandling:
    """Testes para tratamento de erros no sistema RAG."""
    
    @pytest.mark.asyncio
    async def test_embedding_service_error(self):
        """Testa erro no serviço de embedding."""
        mock_repo = AsyncMock()
        mock_embedding_service = AsyncMock()
        mock_embedding_service.embed_text.side_effect = Exception("Embedding service error")
        
        use_case = QueryDocumentsUseCase(mock_repo, mock_embedding_service)
        
        query_request = QueryRequest(query="test query")
        
        with pytest.raises(Exception, match="Embedding service error"):
            await use_case.execute(query_request)
    
    @pytest.mark.asyncio
    async def test_repository_error(self):
        """Testa erro no repositório de chunks."""
        mock_repo = AsyncMock()
        mock_repo.search_similar.side_effect = Exception("Repository error")
        
        mock_embedding_service = AsyncMock()
        mock_embedding_service.embed_text.return_value = AsyncMock()
        mock_embedding_service.embed_text.return_value.to_list.return_value = [0.1, 0.2, 0.3]
        
        use_case = QueryDocumentsUseCase(mock_repo, mock_embedding_service)
        
        query_request = QueryRequest(query="test query")
        
        with pytest.raises(Exception, match="Repository error"):
            await use_case.execute(query_request)
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Testa tratamento de timeouts em operações longas."""
        mock_repo = AsyncMock()
        
        # Simular operação demorada
        async def slow_search(*args, **kwargs):
            await asyncio.sleep(2)  # Simular operação lenta
            return []
        
        mock_repo.search_similar.side_effect = slow_search
        
        mock_embedding_service = AsyncMock()
        mock_embedding_service.embed_text.return_value = AsyncMock()
        mock_embedding_service.embed_text.return_value.to_list.return_value = [0.1, 0.2, 0.3]
        
        use_case = QueryDocumentsUseCase(mock_repo, mock_embedding_service)
        
        query_request = QueryRequest(query="test query")
        
        # Deve completar mesmo com operação lenta
        start_time = time.time()
        response = await use_case.execute(query_request)
        end_time = time.time()
        
        assert response.total_results == 0
        assert end_time - start_time >= 2  # Deve ter esperado a operação lenta


if __name__ == "__main__":
    pytest.main([__file__])
