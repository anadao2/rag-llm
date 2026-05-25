from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ContextManager


class UnitOfWork(ABC, ContextManager):
    """
    UoW Pattern - Gerencia transações em múltiplos repositories.
    Garante consistência quando operações envolvem múltiplas entidades.
    """

    @abstractmethod
    def commit(self) -> None:
        """Confirma todas as operações pendentes."""
        ...

    @abstractmethod
    def rollback(self) -> None:
        """Reverte todas as operações pendentes."""
        ...

    @abstractmethod
    def __enter__(self) -> UnitOfWork:
        """Context manager entry."""
        ...

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - auto-commit ou rollback."""
        ...
