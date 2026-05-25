from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol

from app.domain.services.chunking_service import ChunkingService
from app.domain.services.embedding_service import EmbeddingClient, EmbeddingService
from app.domain.repositories.document_repository import DocumentRepository
from app.domain.repositories.chunk_repository import ChunkRepository


class ServiceFactory(ABC):
    """
    Abstract Factory - Cria famílias de objetos relacionados.
    
    DIP: Clientes dependem desta abstração, não de factories concretas.
    SRP: Fábrica apenas cria objetos, não contém lógica de negócio.
    """

    @abstractmethod
    def create_chunking_service(self) -> ChunkingService:
        """Cria serviço de chunking."""
        ...

    @abstractmethod
    def create_embedding_service(self) -> EmbeddingService:
        """Cria serviço de embedding."""
        ...

    @abstractmethod
    def create_document_repository(self) -> DocumentRepository:
        """Cria repositório de documentos."""
        ...

    @abstractmethod
    def create_chunk_repository(self) -> ChunkRepository:
        """Cria repositório de chunks."""
        ...


class RepositoryFactory(Protocol):
    """
    Protocol para factories de repository (Structural Subtyping).
    ISP: Interface mínima para criação de repositories.
    """

    def create_document_repository(self) -> DocumentRepository:
        ...

    def create_chunk_repository(self) -> ChunkRepository:
        ...
