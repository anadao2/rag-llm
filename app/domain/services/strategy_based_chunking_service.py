from __future__ import annotations

from typing import List

from app.domain.entities.chunk import Chunk
from app.domain.entities.document import Document
from app.domain.strategies.chunking_strategy import ChunkingStrategy, ChunkingConfig


class StrategyBasedChunkingService:
    """
    SRP + OCP: Serviço de chunking desacoplado de implementações específicas.
    
    - SRP: Apenas orquestra a estratégia, não implementa lógica de chunking
    - OCP: Novas estratégias podem ser adicionadas sem modificar este código
    - DIP: Depende da abstração (ChunkingStrategy), não de implementações
    """

    def __init__(self, strategy: ChunkingStrategy) -> None:
        """
        Injeção da estratégia via construtor (DIP).
        
        Args:
            strategy: Estratégia de chunking a ser usada
        """
        self._strategy = strategy

    def chunk_document(
        self,
        document: Document,
        chunk_size: int = 600,
        overlap: int = 100,
        respect_boundaries: bool = True,
    ) -> List[Chunk]:
        """
        Divide documento usando a estratégia configurada.
        
        LSP: Qualquer ChunkingStrategy pode ser usada aqui
        sem alterar o comportamento esperado.
        """
        config = ChunkingConfig(
            chunk_size=chunk_size,
            overlap=overlap,
            respect_boundaries=respect_boundaries,
        )
        
        # Delegar para a estratégia (OCP)
        return self._strategy.chunk(document, config)

    def chunk_documents(
        self,
        documents: List[Document],
        chunk_size: int = 600,
        overlap: int = 100,
        respect_boundaries: bool = True,
    ) -> List[Chunk]:
        """Processa múltiplos documentos."""
        all_chunks: List[Chunk] = []
        
        for doc in documents:
            chunks = self.chunk_document(
                doc,
                chunk_size=chunk_size,
                overlap=overlap,
                respect_boundaries=respect_boundaries,
            )
            all_chunks.extend(chunks)
        
        return all_chunks

    def get_strategy_name(self) -> str:
        """Retorna nome da estratégia em uso."""
        return self._strategy.get_name()
