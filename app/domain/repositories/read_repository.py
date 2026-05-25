from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, TypeVar, Generic

T = TypeVar("T")
ID = TypeVar("ID")


class ReadRepository(ABC, Generic[T, ID]):
    """
    ISP: Interface Segregation Principle
    Interface apenas para operações de leitura.
    Clientes que só leem não precisam depender de métodos de escrita.
    """

    @abstractmethod
    def find_by_id(self, id: ID) -> T | None:
        """Busca entidade pelo ID."""
        ...

    @abstractmethod
    def find_all(self) -> List[T]:
        """Retorna todas as entidades."""
        ...

    @abstractmethod
    def count(self) -> int:
        """Retorna quantidade total."""
        ...

    @abstractmethod
    def exists(self, id: ID) -> bool:
        """Verifica se entidade existe."""
        ...
