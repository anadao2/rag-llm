"""Teste End-to-End do fluxo completo de ingestão."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.application.dto.ingest_dto import IngestRequestDTO
from app.application.use_cases.ingest_documents import IngestDocumentsUseCase
from app.domain.entities.document import Document
from app.domain.services.chunking_service import ChunkingService
from app.domain.services.embedding_service import EmbeddingService
from app.infrastructure.persistence.faiss_chunk_repository import FaissChunkRepository
from app.infrastructure.persistence.json_document_repository import JsonDocumentRepository
from app.infrastructure.external.openai_embedder import OpenAIEmbedder


def test_full_ingest_flow_with_mock():
    """Testa fluxo completo de ingestão com mock."""
    print("\n>> Running E2E test with mock embeddings...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        docs_dir = Path(tmpdir) / "docs"
        docs_dir.mkdir()
        
        # Criar arquivo de teste
        test_file = docs_dir / "test_doc.txt"
        test_content = "This is a test document. " * 20  # ~460 chars
        test_file.write_text(test_content, encoding="utf-8")
        
        # Configurar repositórios
        faiss_dir = Path(tmpdir) / "faiss"
        doc_repo = JsonDocumentRepository(base_dir=faiss_dir)
        chunk_repo = FaissChunkRepository(base_dir=faiss_dir)
        
        # Criar mock para OpenAI
        mock_embedder = Mock(spec=OpenAIEmbedder)
        # Retornar vetores dummy de 1536 dimensões (padrão text-embedding-3-small)
        def mock_embed(texts, model):
            return [[0.1] * 1536 for _ in texts]
        mock_embedder.embed = mock_embed
        
        # Criar use case
        use_case = IngestDocumentsUseCase(
            document_repo=doc_repo,
            chunk_repo=chunk_repo,
            embedding_client=mock_embedder,
        )
        
        # Criar request
        request = IngestRequestDTO(
            docs_dir=docs_dir,
            chunk_size=200,
            chunk_overlap=50,
            embedding_model="text-embedding-3-small",
        )
        
        # Executar
        result = use_case.execute(request)
        
        # Verificar resultados
        assert result.documents_count == 1, f"Expected 1 document, got {result.documents_count}"
        assert result.chunks_count > 0, f"Expected chunks, got {result.chunks_count}"
        
        # Verificar persistência
        assert doc_repo.count() == 1, "Document should be persisted"
        assert chunk_repo.count() == result.chunks_count, "Chunks should be persisted"
        assert chunk_repo.is_ready(), "Vector store should be ready"
        
        print(f"[PASS] E2E Test passed!")
        print(f"   - Documents: {result.documents_count}")
        print(f"   - Chunks: {result.chunks_count}")
        print(f"   - Chunks per doc: {result.chunks_count / result.documents_count:.1f}")


def test_chunking_with_strategy_pattern():
    """Testa chunking usando Strategy Pattern (OCP)."""
    print("\n>> Testing chunking with Strategy Pattern...")
    
    from app.domain.strategies import SentenceAwareChunking, FixedSizeChunking
    from app.domain.services.strategy_based_chunking_service import StrategyBasedChunkingService
    
    doc = Document.create(
        file_name="test.txt",
        source_path=Path("/test.txt"),
        content="First sentence here. Second sentence follows. Third one here. And final one.",
    )
    
    # Testar ambas as estratégias (LSP)
    strategies = [
        SentenceAwareChunking(),
        FixedSizeChunking(),
    ]
    
    for strategy in strategies:
        service = StrategyBasedChunkingService(strategy)
        chunks = service.chunk_document(doc, chunk_size=30, overlap=5)
        
        assert len(chunks) > 0, f"{strategy.get_name()} should create chunks"
        assert all(len(c.text.strip()) > 0 for c in chunks), "All chunks should have content"
        
        print(f"  - {strategy.get_name()}: {len(chunks)} chunks")
    
    print("[PASS] Strategy Pattern chunking works!")


def test_vector_search():
    """Testa busca vetorial."""
    print("\n>> Testing vector search...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        chunk_repo = FaissChunkRepository(base_dir=Path(tmpdir))
        
        # Criar chunks com embeddings
        from app.domain.entities.chunk import Chunk
        from app.domain.value_objects.embedding import Embedding
        
        doc_id = Document.create("t.txt", Path("/t.txt"), "content").doc_id
        
        chunks = []
        for i in range(5):
            chunk = Chunk.create(
                doc_id=doc_id,
                text=f"Text number {i}",
                order=i,
                start_char=i*10,
                end_char=i*10+10,
                file_name="test.txt",
                source_path="/test.txt",
            )
            # Criar embedding com valores diferentes para cada chunk
            vector = [0.0] * 1536
            vector[i] = 1.0  # Cada chunk tem um valor distinto
            embedding = Embedding.from_list(vector, "test-model")
            chunk.attach_embedding(embedding)
            chunks.append(chunk)
        
        # Salvar
        chunk_repo.save_batch(chunks)
        
        # Buscar
        query = [0.0] * 1536
        query[2] = 1.0  # Deve encontrar chunk 2
        results = chunk_repo.search_similar(query, top_k=3)
        
        assert len(results) > 0, "Should find results"
        print(f"[PASS] Vector search test passed (found {len(results)} results)")


def test_specifications_in_pipeline():
    """Testa Specifications no pipeline de documentos."""
    print("\n>> Testing Specifications in pipeline...")
    
    from app.domain.specifications import PROCESSED, TXT_FILES, FAILED
    
    # Criar documentos de teste
    doc1 = Document.create("processed.txt", Path("/p.txt"), "content")
    doc1.mark_as_completed()
    
    doc2 = Document.create("pending.txt", Path("/p2.txt"), "content")
    # status = pending (default)
    
    doc3 = Document.create("failed.pdf", Path("/f.pdf"), "content")
    doc3.mark_as_failed("error")
    
    docs = [doc1, doc2, doc3]
    
    # Compor especificações (OCP)
    processed_txt = PROCESSED.and_(TXT_FILES)
    
    # Aplicar filtros
    processed_docs = [d for d in docs if processed_txt.is_satisfied_by(d)]
    failed_docs = [d for d in docs if FAILED.is_satisfied_by(d)]
    
    assert len(processed_docs) == 1, "Should find 1 processed txt"
    assert processed_docs[0].file_name == "processed.txt"
    assert len(failed_docs) == 1, "Should find 1 failed"
    assert failed_docs[0].file_name == "failed.pdf"
    
    print(f"[PASS] Specifications filtering works! (processed: {len(processed_docs)}, failed: {len(failed_docs)})")


def run_all_tests():
    """Roda todos os testes E2E."""
    print("\n" + "="*50)
    print("TEST END-TO-END TESTS")
    print("="*50)
    
    test_full_ingest_flow_with_mock()
    test_chunking_with_strategy_pattern()
    test_specifications_in_pipeline()
    test_vector_search()
    
    print("\n" + "="*50)
    print("[PASS] ALL E2E TESTS PASSED!")
    print("="*50)


if __name__ == "__main__":
    run_all_tests()


