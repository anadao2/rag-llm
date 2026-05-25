from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict

from app.domain.events.domain_event import DomainEvent, DomainEventHandler


@dataclass(frozen=True)
class DocumentCreated(DomainEvent):
    """Evento: Documento foi criado."""
    file_name: str = ""
    content_length: int = 0


@dataclass(frozen=True)
class DocumentProcessingStarted(DomainEvent):
    """Evento: Processamento de documento iniciado."""
    started_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class DocumentProcessingCompleted(DomainEvent):
    """Evento: Documento processado com sucesso."""
    completed_at: datetime = field(default_factory=datetime.utcnow)
    chunks_count: int = 0


@dataclass(frozen=True)
class DocumentProcessingFailed(DomainEvent):
    """Evento: Falha no processamento de documento."""
    error_message: str = ""
    failed_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class ChunksCreated(DomainEvent):
    """Evento: Chunks foram criados para um documento."""
    doc_id: str = ""
    chunks_count: int = 0
    strategy_used: str = ""


# Handlers de exemplo
class LoggingEventHandler(DomainEventHandler[DomainEvent]):
    """Handler que loga todos os eventos."""

    def handle(self, event: DomainEvent) -> None:
        print(f"[EVENT] {type(event).__name__}: {event.aggregate_id}")

    def event_type(self) -> type:
        return DomainEvent


class MetricsEventHandler(DomainEventHandler[DocumentProcessingCompleted]):
    """Handler que coleta métricas de processamento."""

    def __init__(self) -> None:
        self._total_processed = 0
        self._total_chunks = 0

    def handle(self, event: DocumentProcessingCompleted) -> None:
        self._total_processed += 1
        self._total_chunks += event.chunks_count

    def event_type(self) -> type:
        return DocumentProcessingCompleted

    def get_stats(self) -> Dict[str, int]:
        return {
            "total_documents": self._total_processed,
            "total_chunks": self._total_chunks,
        }
