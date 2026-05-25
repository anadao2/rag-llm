"""Testes unitários para o Domain Layer."""
from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.domain.entities.document import Document
from app.domain.entities.chunk import Chunk
from app.domain.value_objects.document_id import DocumentId
from app.domain.value_objects.chunk_id import ChunkId
from app.domain.value_objects.embedding import Embedding
from app.domain.services.chunking_service import ChunkingService


def test_document_id_generation():
    """Testa geração de DocumentId."""
    doc_id = DocumentId.generate()
    assert doc_id.value is not None
    assert len(doc_id.value) == 36  # UUID format
    print("[OK] DocumentId generation works")


def test_document_creation():
    """Testa criação de Document."""
    doc = Document.create(
        file_name="test.txt",
        source_path=Path("/test/test.txt"),
        content="This is test content",
        metadata={"author": "test"},
    )
    assert doc.file_name == "test.txt"
    assert doc.content == "This is test content"
    assert doc.status == "pending"
    print("[OK] Document creation works")


def test_document_lifecycle():
    """Testa lifecycle de Document."""
    doc = Document.create(
        file_name="test.txt",
        source_path=Path("/test/test.txt"),
        content="content",
    )
    doc.mark_as_processing()
    assert doc.status == "processing"
    
    doc.mark_as_completed()
    assert doc.status == "completed"
    assert doc.processed_at is not None
    print("[OK] Document lifecycle works")


def test_chunk_creation():
    """Testa criação de Chunk."""
    doc_id = DocumentId.generate()
    chunk = Chunk.create(
        doc_id=doc_id,
        text="This is a chunk of text",
        order=0,
        start_char=0,
        end_char=23,
        file_name="test.txt",
        source_path="/test/test.txt",
    )
    assert chunk.text == "This is a chunk of text"
    assert chunk.order == 0
    assert chunk.doc_id == doc_id
    assert chunk.has_embedding() is False
    print("[OK] Chunk creation works")


def test_chunk_with_embedding():
    """Testa anexar embedding a Chunk."""
    doc_id = DocumentId.generate()
    chunk = Chunk.create(
        doc_id=doc_id,
        text="Text for embedding",
        order=0,
        start_char=0,
        end_char=18,
        file_name="test.txt",
        source_path="/test/test.txt",
    )
    
    embedding = Embedding.from_list([0.1, 0.2, 0.3], "test-model")
    chunk.attach_embedding(embedding)
    
    assert chunk.has_embedding() is True
    assert chunk.embedding.model == "test-model"
    assert chunk.embedding.dimensions == 3
    print("[OK] Chunk with embedding works")


def test_chunking_service():
    """Testa chunking de documento."""
    doc = Document.create(
        file_name="long.txt",
        source_path=Path("/test/long.txt"),
        content="This is a long text. " * 20,  # ~500 chars
    )
    
    chunking_service = ChunkingService(chunk_size=100, overlap=20)
    chunks = chunking_service.chunk_document(doc)
    
    assert len(chunks) > 0
    assert all(chunk.doc_id == doc.doc_id for chunk in chunks)
    print(f"[OK] Chunking service works ({len(chunks)} chunks created)")


def test_embedding_value_object():
    """Testa Value Object Embedding."""
    embedding = Embedding.from_list([0.1, 0.2, 0.3, 0.4], "text-embedding-3-small")
    assert embedding.dimensions == 4
    assert embedding.model == "text-embedding-3-small"
    assert len(embedding.vector) == 4
    print("[OK] Embedding Value Object works")


def test_strategies():
    """Testa Strategy Pattern para chunking."""
    from app.domain.strategies import SentenceAwareChunking, FixedSizeChunking
    from app.domain.services.strategy_based_chunking_service import StrategyBasedChunkingService
    
    doc = Document.create(
        file_name="test.txt",
        source_path=Path("/test.txt"),
        content="First sentence. Second sentence. Third one.",
    )
    
    # Testar diferentes estrategias (LSP)
    strategies = [
        SentenceAwareChunking(),
        FixedSizeChunking(),
    ]
    
    for strategy in strategies:
        service = StrategyBasedChunkingService(strategy)
        chunks = service.chunk_document(doc, chunk_size=50, overlap=10)
        
        assert len(chunks) > 0
        assert all(isinstance(c, Chunk) for c in chunks)
        print(f"[OK] Strategy {strategy.get_name()} works")


def test_specifications():
    """Testa Specification Pattern."""
    from app.domain.specifications import (
        DocumentProcessedSpecification,
        DocumentByExtensionSpecification,
        PROCESSED,
    )
    
    # Criar documentos de teste
    doc1 = Document.create("file.txt", Path("/f.txt"), "content")
    doc1.mark_as_completed()
    
    doc2 = Document.create("file.pdf", Path("/f.pdf"), "content")
    # pending
    
    # Testar especificacoes individuais
    processed_spec = DocumentProcessedSpecification()
    assert processed_spec.is_satisfied_by(doc1) is True
    assert processed_spec.is_satisfied_by(doc2) is False
    
    # Testar especificacao pre-definida
    assert PROCESSED.is_satisfied_by(doc1) is True
    
    # Testar extensao
    txt_spec = DocumentByExtensionSpecification(".txt")
    assert txt_spec.is_satisfied_by(doc1) is True
    assert txt_spec.is_satisfied_by(doc2) is False
    
    print("[OK] Specification pattern works")


def run_all_tests():
    """Roda todos os testes do domain."""
    print("\n=== Domain Layer Tests ===")
    test_document_id_generation()
    test_document_creation()
    test_document_lifecycle()
    test_chunk_creation()
    test_chunk_with_embedding()
    test_chunking_service()
    test_embedding_value_object()
    test_strategies()
    test_specifications()
    print("\n[PASS] All Domain tests passed!")


if __name__ == "__main__":
    run_all_tests()

