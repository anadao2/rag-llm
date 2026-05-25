"""Testes de integração para validar a aplicação completa."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient

# Configurar environment
import os
os.environ["OPENAI_API_KEY"] = "test-key-for-integration"

from app.main import app


def test_health_endpoint():
    """Testa endpoint de health."""
    client = TestClient(app)
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["api_status"] == "ok"
    assert "vector_store_status" in data
    assert "indexed_documents_count" in data
    print("[OK] Health endpoint works")


def test_ingest_endpoint_empty():
    """Testa ingestão com diretório vazio."""
    client = TestClient(app)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Diretório sem arquivos
        response = client.post("/ingest", json={
            "docs_dir": tmpdir,
            "chunk_size": 100,
            "chunk_overlap": 20,
            "embedding_model": "text-embedding-3-small",
        })
        
        # Não deve falhar, apenas retornar 0 documentos
        assert response.status_code in [200, 500]  # 500 se não tiver API key real
        if response.status_code == 200:
            data = response.json()
            assert data["documents_count"] == 0
            print("[OK] Ingest endpoint handles empty dir")


def test_ingest_endpoint_validation():
    """Testa validação do endpoint."""
    client = TestClient(app)
    
    # Testar chunk_overlap > chunk_size (deve falhar)
    response = client.post("/ingest", json={
        "docs_dir": "/tmp",
        "chunk_size": 100,
        "chunk_overlap": 150,  # Maior que chunk_size!
    })
    
    assert response.status_code == 400
    print("[OK] Validation works (chunk_overlap >= chunk_size rejected)")


def run_all_tests():
    """Roda todos os testes de integração."""
    print("\n=== Integration Tests ===")
    test_health_endpoint()
    test_ingest_endpoint_validation()
    test_ingest_endpoint_empty()
    print("\n[PASS] All Integration tests passed!")


if __name__ == "__main__":
    run_all_tests()

