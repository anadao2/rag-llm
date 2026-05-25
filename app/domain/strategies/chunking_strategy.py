from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

from app.domain.entities.chunk import Chunk
from app.domain.entities.document import Document


@dataclass(frozen=True)
class ChunkingConfig:
    """Value Object para configuração de chunking."""
    chunk_size: int = 600
    overlap: int = 100
    respect_boundaries: bool = True  # Respeitar limites de sentença


class ChunkingStrategy(ABC):
    """
    OCP: Open/Closed Principle
    Aberto para extensão (novas estratégias), fechado para modificação.
    Strategy Pattern permite adicionar novos algoritmos sem mudar código existente.
    """

    @abstractmethod
    def chunk(self, document: Document, config: ChunkingConfig) -> List[Chunk]:
        """
        Divide documento em chunks segundo a estratégia.
        
        Args:
            document: Documento a ser dividido
            config: Configurações de chunking
            
        Returns:
            Lista de chunks gerados
        """
        ...

    @abstractmethod
    def get_name(self) -> str:
        """Retorna nome identificador da estratégia."""
        ...
