from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, TypeVar, Generic

T = TypeVar("T")


class WriteRepository(ABC, Generic[T]):
    """
    ISP: Interface Segregation Principle
    Interface apenas para operações de escrita.
    Clientes que só escrevem não precisam depender de métodos de leitura.
    """

    @abstractmethod
    def save(self, entity: T) -> None:
        """Salva ou atualiza uma entidade."""
        ...

    @abstractmethod
    def save_batch(self, entities: List[T]) -> None:
        """Salva múltiplas entidades em lote."""
        ...

    @abstractmethod
    def delete(self, entity: T) -> None:
        """Remove uma entidade."""
        ...

    @abstractmethod
    def delete_by_id(self, id: str) -> None:
        """Remove entidade pelo ID."""
        ...
