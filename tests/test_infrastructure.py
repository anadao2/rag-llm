"""Testes unitários para o Infrastructure Layer."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.domain.entities.document import Document
from app.domain.value_objects.document_id import DocumentId
from app.infrastructure.persistence.json_document_repository import JsonDocumentRepository
from app.infrastructure.persistence.mappers.document_mapper import DocumentMapper
from app.infrastructure.persistence.mappers.chunk_mapper import ChunkMapper


def test_document_mapper():
    """Testa mapeamento Document <-> Record."""
    mapper = DocumentMapper()
    
    doc = Document.create(
        file_name="test.txt",
        source_path=Path("/test/test.txt"),
        content="test content",
        metadata={"key": "value"},
    )
    
    # Para record
    record = mapper.to_record(doc)
    assert record["file_name"] == "test.txt"
    assert record["content"] == "test content"
    assert record["metadata"]["key"] == "value"
    
    # De volta para domain
    restored = mapper.to_domain(record)
    assert restored.file_name == doc.file_name
    assert restored.doc_id == doc.doc_id
    print("[OK] DocumentMapper works")


def test_json_document_repository():
    """Testa JSON Document Repository."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = JsonDocumentRepository(base_dir=Path(tmpdir))
        
        # Criar documento
        doc = Document.create(
            file_name="test.txt",
            source_path=Path("/test/test.txt"),
            content="content",
        )
        
        # Salvar
        repo.save(doc)
        assert repo.count() == 1
        
        # Buscar
        found = repo.find_by_id(doc.doc_id)
        assert found is not None
        assert found.file_name == "test.txt"
        
        # Verificar existência
        assert repo.exists(doc.doc_id) is True
        
        # Buscar todos
        all_docs = repo.find_all()
        assert len(all_docs) == 1
        
        print("[OK] JsonDocumentRepository works")


def test_repository_batch_save():
    """Testa save em lote."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = JsonDocumentRepository(base_dir=Path(tmpdir))
        
        docs = [
            Document.create(f"doc{i}.txt", Path(f"/test/{i}.txt"), f"content {i}")
            for i in range(5)
        ]
        
        repo.save_batch(docs)
        assert repo.count() == 5
        
        print("[OK] Repository batch save works")


def run_all_tests():
    """Roda todos os testes da infrastructure layer."""
    print("\n=== Infrastructure Layer Tests ===")
    test_document_mapper()
    test_json_document_repository()
    test_repository_batch_save()
    print("\n[PASS] All Infrastructure tests passed!")


if __name__ == "__main__":
    run_all_tests()

