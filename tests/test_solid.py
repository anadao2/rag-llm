"""
Testes para validar principios SOLID.

S - Single Responsibility Principle
O - Open/Closed Principle
L - Liskov Substitution Principle
I - Interface Segregation Principle
D - Dependency Inversion Principle
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.domain.entities.document import Document
from app.domain.entities.chunk import Chunk
from app.domain.strategies.chunking_strategy import ChunkingConfig
from app.domain.strategies.sentence_aware_chunking import SentenceAwareChunking
from app.domain.strategies.fixed_size_chunking import FixedSizeChunking
from app.domain.services.strategy_based_chunking_service import StrategyBasedChunkingService
from app.domain.specifications.specification import AndSpecification, OrSpecification
from app.domain.specifications.document_specifications import (
    DocumentProcessedSpecification,
    DocumentByExtensionSpecification,
    PROCESSED,
    TXT_FILES,
)
from app.domain.events.domain_event import EventBus
from app.domain.events.document_events import (
    DocumentCreated,
    DocumentProcessingCompleted,
    LoggingEventHandler,
    MetricsEventHandler,
)


def test_srp_single_responsibility():
    """
    SRP: Uma classe deve ter apenas um motivo para mudar.
    
    - ChunkingStrategy: apenas algoritmo de chunking
    - Specification: apenas regras de filtro
    - DomainEvent: apenas dados de evento
    """
    print("\n[SRP] Testing Single Responsibility Principle...")
    
    # Strategy tem apenas chunk()
    strategy = SentenceAwareChunking()
    assert hasattr(strategy, 'chunk')
    assert hasattr(strategy, 'get_name')
    assert not hasattr(strategy, 'save')  # Nao deve salvar
    assert not hasattr(strategy, 'load')  # Nao deve carregar
    
    # Specification tem apenas is_satisfied_by
    spec = DocumentProcessedSpecification()
    assert hasattr(spec, 'is_satisfied_by')
    assert not hasattr(spec, 'save')
    assert not hasattr(spec, 'delete')
    
    print("  [OK] Classes have single responsibilities")


def test_ocp_open_closed():
    """
    OCP: Aberto para extensao, fechado para modificacao.
    
    - Novas estrategias de chunking sem modificar o service
    - Novas specifications sem modificar queries
    """
    print("\n[OCP] Testing Open/Closed Principle...")
    
    doc = Document.create(
        file_name="test.txt",
        source_path=Path("/test.txt"),
        content="Sentence one. Sentence two. Sentence three.",
    )
    
    # Criar service com diferentes estrategias (extensao)
    sentence_strategy = SentenceAwareChunking()
    fixed_strategy = FixedSizeChunking()
    
    service1 = StrategyBasedChunkingService(sentence_strategy)
    service2 = StrategyBasedChunkingService(fixed_strategy)
    
    # Ambos funcionam sem modificar o service
    chunks1 = service1.chunk_document(doc, chunk_size=20, overlap=5)
    chunks2 = service2.chunk_document(doc, chunk_size=20, overlap=5)
    
    assert len(chunks1) > 0
    assert len(chunks2) > 0
    assert service1.get_strategy_name() == "sentence-aware"
    assert service2.get_strategy_name() == "fixed-size"
    
    print(f"  [OK] Extended with {len(chunks1)} chunks (sentence) and {len(chunks2)} chunks (fixed)")


def test_lsp_liskov_substitution():
    """
    LSP: Subclasses devem ser substituive por suas bases.
    
    - Qualquer ChunkingStrategy pode ser usada no service
    - Comportamento esperado eh mantido
    """
    print("\n[LSP] Testing Liskov Substitution Principle...")
    
    doc = Document.create(
        file_name="test.txt",
        source_path=Path("/test.txt"),
        content="Content for testing LSP. Multiple sentences here. And another one.",
    )
    
    strategies = [
        SentenceAwareChunking(),
        FixedSizeChunking(),
    ]
    
    for strategy in strategies:
        # LSP: Todas as estrategias funcionam no mesmo servico
        service = StrategyBasedChunkingService(strategy)
        chunks = service.chunk_document(doc, chunk_size=30, overlap=5)
        
        # Invariantes: sempre retorna lista de chunks
        assert isinstance(chunks, list)
        assert all(isinstance(c, Chunk) for c in chunks)
        
        print(f"  [OK] {strategy.get_name()} works as ChunkingStrategy")


def test_isp_interface_segregation():
    """
    ISP: Interfaces especificas sao melhores que interfaces gerais.
    
    - ReadRepository: apenas leitura
    - WriteRepository: apenas escrita
    - Specification: apenas filtro
    - ChunkingStrategy: apenas chunking
    """
    print("\n[ISP] Testing Interface Segregation Principle...")
    
    from app.domain.repositories.read_repository import ReadRepository
    from app.domain.repositories.write_repository import WriteRepository
    
    # ReadRepository tem apenas metodos de leitura
    read_methods = {'find_by_id', 'find_all', 'count', 'exists'}
    actual_read = {m for m in dir(ReadRepository) if not m.startswith('_')}
    assert actual_read >= read_methods
    
    # WriteRepository tem apenas metodos de escrita
    write_methods = {'save', 'save_batch', 'delete', 'delete_by_id'}
    actual_write = {m for m in dir(WriteRepository) if not m.startswith('_')}
    assert actual_write >= write_methods
    
    # Nao ha metodos de escrita em ReadRepository
    assert not hasattr(ReadRepository, 'save')
    assert not hasattr(ReadRepository, 'delete')
    
    print("  [OK] Read and Write interfaces are segregated")


def test_dip_dependency_inversion():
    """
    DIP: Dependa de abstracoes, nao de concretos.
    
    - StrategyBasedChunkingService depende de ChunkingStrategy (abstracao)
    - Use Cases dependem de Repository interfaces
    - DomainEventHandler depende de DomainEvent
    """
    print("\n[DIP] Testing Dependency Inversion Principle...")
    
    from app.domain.strategies.chunking_strategy import ChunkingStrategy
    
    # DIP: Service depende da abstracao, nao da implementacao
    doc = Document.create("test.txt", Path("/test.txt"), "content")
    
    # Posso injetar qualquer implementacao de ChunkingStrategy
    abstract_type = ChunkingStrategy
    concrete_impl = SentenceAwareChunking()
    
    assert isinstance(concrete_impl, abstract_type)
    
    service = StrategyBasedChunkingService(concrete_impl)
    assert service._strategy is concrete_impl
    
    print("  [OK] Service depends on ChunkingStrategy abstraction")


def test_specification_composition():
    """
    OCP + SRP: Specifications sao combinaveis sem modificacao.
    """
    print("\n[Composition] Testing Specification pattern...")
    
    doc1 = Document.create("test.txt", Path("/t.txt"), "content")
    doc1.mark_as_completed()
    
    doc2 = Document.create("other.pdf", Path("/t.pdf"), "content")
    
    # Composicao: Processed AND TXT (AND)
    and_spec = PROCESSED.and_(TXT_FILES)
    assert and_spec.is_satisfied_by(doc1) is True
    assert and_spec.is_satisfied_by(doc2) is False  # Nao eh txt
    
    # Composicao: Processed OR PDF (OR)
    pdf_spec = DocumentByExtensionSpecification(".pdf")
    or_spec = PROCESSED.or_(pdf_spec)
    assert or_spec.is_satisfied_by(doc1) is True  # Processed
    assert or_spec.is_satisfied_by(doc2) is True  # PDF
    
    print("  [OK] Specifications compose with AND/OR")


def test_event_driven_architecture():
    """
    DIP + SRP: Event bus desacopla publicadores de consumidores.
    """
    print("\n[Events] Testing Event-Driven Architecture...")
    
    event_bus = EventBus()
    handler = MetricsEventHandler()
    
    # DIP: Publicador nao conhece consumidor
    event_bus.subscribe(DocumentProcessingCompleted, handler.handle)
    
    # Publicar evento
    event = DocumentProcessingCompleted(
        event_id="evt-1",
        aggregate_id="doc-1",
        chunks_count=5,
    )
    event_bus.publish(event)
    
    # Handler processou
    stats = handler.get_stats()
    assert stats["total_documents"] == 1
    assert stats["total_chunks"] == 5
    
    print("  [OK] Event bus decouples publishers and handlers")


def run_all_tests():
    """Roda todos os testes SOLID."""
    print("\n" + "="*60)
    print("SOLID PRINCIPLES VALIDATION")
    print("="*60)
    
    test_srp_single_responsibility()
    test_ocp_open_closed()
    test_lsp_liskov_substitution()
    test_isp_interface_segregation()
    test_dip_dependency_inversion()
    test_specification_composition()
    test_event_driven_architecture()
    
    print("\n" + "="*60)
    print("[PASS] All SOLID principles validated!")
    print("="*60)


if __name__ == "__main__":
    run_all_tests()
