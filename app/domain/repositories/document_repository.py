from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from app.domain.entities.document import Document
from app.domain.value_objects.document_id import DocumentId


class DocumentRepository(ABC):
    """
    Interface (Port) para persistência de Documents.
    Implementações concretas ficam na camada Infrastructure.
    """

    @abstractmethod
    def save(self, document: Document) -> None:
        """Salva ou atualiza um documento."""
        ...

    @abstractmethod
    def save_batch(self, documents: List[Document]) -> None:
        """Salva múltiplos documentos em lote."""
        ...

    @abstractmethod
    def find_by_id(self, doc_id: DocumentId) -> Document | None:
        """Busca documento pelo ID."""
        ...

    @abstractmethod
    def find_all(self) -> List[Document]:
        """Retorna todos os documentos."""
        ...

    @abstractmethod
    def count(self) -> int:
        """Retorna quantidade total de documentos."""
        ...

    @abstractmethod
    def exists(self, doc_id: DocumentId) -> bool:
        """Verifica se documento existe."""
        ...
