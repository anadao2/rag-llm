from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, TypeVar, Generic, Callable, Dict, Any


@dataclass(frozen=True)
class DomainEvent:
    """
    Evento de domínio - representa algo que aconteceu no passado.
    
    SRP: Eventos são objetos de transferência de dados puros.
    OCP: Novos tipos de eventos podem ser adicionados sem modificar handlers existentes.
    """
    event_id: str
    aggregate_id: str
    occurred_on: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


T = TypeVar("T", bound=DomainEvent)


class DomainEventHandler(ABC, Generic[T]):
    """
    Handler para processar eventos de domínio.
    
    SRP: Cada handler processa um tipo específico de evento.
    OCP: Novos handlers podem ser adicionados sem modificar código existente.
    """

    @abstractmethod
    def handle(self, event: T) -> None:
        """Processa o evento."""
        ...

    @abstractmethod
    def event_type(self) -> type:
        """Retorna o tipo de evento que este handler processa."""
        ...


class EventBus:
    """
    Bus de eventos - desacoplamento entre publicadores e assinantes.
    
    DIP: Publicadores dependem de DomainEvent, não de handlers específicos.
    """

    def __init__(self) -> None:
        self._handlers: Dict[type, List[Callable[[DomainEvent], None]]] = {}

    def subscribe(self, event_type: type, handler: Callable[[DomainEvent], None]) -> None:
        """Registra handler para um tipo de evento."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def publish(self, event: DomainEvent) -> None:
        """Publica evento para todos os handlers registrados."""
        event_type = type(event)
        handlers = self._handlers.get(event_type, [])
        
        for handler in handlers:
            handler(event)

    def clear(self) -> None:
        """Remove todos os handlers (útil para testes)."""
        self._handlers.clear()
