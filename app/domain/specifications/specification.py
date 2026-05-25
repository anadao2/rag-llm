from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List

T = TypeVar("T")


class Specification(ABC, Generic[T]):
    """
    Specification Pattern - SRP + OCP
    Encapsula regras de seleção/filtro em objetos reutilizáveis.
    
    Permite combinar especificações (AND, OR, NOT) sem modificar
    as classes que as usam.
    """

    @abstractmethod
    def is_satisfied_by(self, candidate: T) -> bool:
        """Verifica se o candidato satisfaz a especificação."""
        ...

    def and_(self, other: Specification[T]) -> AndSpecification[T]:
        """Combina com AND (composição)."""
        return AndSpecification(self, other)

    def or_(self, other: Specification[T]) -> OrSpecification[T]:
        """Combina com OR (composição)."""
        return OrSpecification(self, other)

    def not_(self) -> NotSpecification[T]:
        """Nega a especificação."""
        return NotSpecification(self)


class AndSpecification(Specification[T]):
    """Especificação composta: A AND B."""

    def __init__(self, left: Specification[T], right: Specification[T]) -> None:
        self._left = left
        self._right = right

    def is_satisfied_by(self, candidate: T) -> bool:
        return self._left.is_satisfied_by(candidate) and self._right.is_satisfied_by(candidate)


class OrSpecification(Specification[T]):
    """Especificação composta: A OR B."""

    def __init__(self, left: Specification[T], right: Specification[T]) -> None:
        self._left = left
        self._right = right

    def is_satisfied_by(self, candidate: T) -> bool:
        return self._left.is_satisfied_by(candidate) or self._right.is_satisfied_by(candidate)


class NotSpecification(Specification[T]):
    """Especificação negada: NOT A."""

    def __init__(self, spec: Specification[T]) -> None:
        self._spec = spec

    def is_satisfied_by(self, candidate: T) -> bool:
        return not self._spec.is_satisfied_by(candidate)
