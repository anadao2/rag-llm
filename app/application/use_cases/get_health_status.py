from __future__ import annotations

from dataclasses import dataclass

from app.domain.repositories.chunk_repository import ChunkRepository
from app.domain.repositories.document_repository import DocumentRepository


@dataclass(frozen=True, slots=True)
class HealthStatusDTO:
    api_status: str
    vector_store_status: str
    indexed_documents_count: int
    indexed_chunks_count: int


class GetHealthStatusUseCase:
    """
    Application Service - Consulta status de saúde do sistema.
    """

    def __init__(
        self,
        document_repo: DocumentRepository,
        chunk_repo: ChunkRepository,
    ) -> None:
        self.document_repo = document_repo
        self.chunk_repo = chunk_repo

    def execute(self) -> HealthStatusDTO:
        is_ready = self.chunk_repo.is_ready()
        vector_status = "ok" if is_ready else "empty"

        return HealthStatusDTO(
            api_status="ok",
            vector_store_status=vector_status,
            indexed_documents_count=self.document_repo.count(),
            indexed_chunks_count=self.chunk_repo.count(),
        )
