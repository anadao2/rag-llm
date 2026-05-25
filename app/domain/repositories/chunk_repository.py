from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from app.domain.entities.chunk import Chunk
from app.domain.value_objects.chunk_id import ChunkId
from app.domain.value_objects.document_id import DocumentId


class ChunkRepository(ABC):
    """
    Interface (Port) para persistência vetorial de Chunks.
    Implementações concretas usam FAISS, Pinecone, etc.
    """

    @abstractmethod
    def save(self, chunk: Chunk) -> None:
        """Salva chunk com seu embedding."""
        ...

    @abstractmethod
    def save_batch(self, chunks: List[Chunk]) -> None:
        """Salva múltiplos chunks em lote."""
        ...

    @abstractmethod
    def find_by_id(self, chunk_id: ChunkId) -> Chunk | None:
        """Busca chunk pelo ID."""
        ...

    @abstractmethod
    def find_by_document_id(self, doc_id: DocumentId) -> List[Chunk]:
        """Busca todos os chunks de um documento."""
        ...

    @abstractmethod
    def search_similar(
        self,
        query_embedding: List[float],
        top_k: int = 5,
    ) -> List[Chunk]:
        """Busca chunks similares via similaridade vetorial."""
        ...

    @abstractmethod
    def count(self) -> int:
        """Retorna quantidade total de chunks indexados."""
        ...

    @abstractmethod
    def is_ready(self) -> bool:
        """Verifica se repositório está pronto para uso."""
        ...
