from __future__ import annotations

from pathlib import Path
from typing import List

from app.application.dto.ingest_dto import IngestRequestDTO, IngestResultDTO
from app.domain.entities.chunk import Chunk
from app.domain.entities.document import Document
from app.domain.repositories.chunk_repository import ChunkRepository
from app.domain.repositories.document_repository import DocumentRepository
from app.domain.services.chunking_service import ChunkingService
from app.domain.services.embedding_service import EmbeddingClient, EmbeddingService


class IngestDocumentsUseCase:
    """
    Application Service - Orquestra o caso de uso de ingestão.
    Coordena Domain Services e Repositories, sem lógica de negócio própria.
    """

    def __init__(
        self,
        document_repo: DocumentRepository,
        chunk_repo: ChunkRepository,
        embedding_client: EmbeddingClient,
    ) -> None:
        self.document_repo = document_repo
        self.chunk_repo = chunk_repo
        self.embedding_client = embedding_client

    def execute(self, request: IngestRequestDTO) -> IngestResultDTO:
        """
        Executa o fluxo completo de ingestão:
        1. Carrega documentos
        2. Cria chunks
        3. Gera embeddings
        4. Persiste tudo
        """
        # 1. Carregar documentos
        documents = self._load_documents(request.docs_dir)

        if not documents:
            return IngestResultDTO(
                documents_count=0,
                chunks_count=0,
                processed_document_ids=[],
            )

        # 2. Chunking
        chunking_service = ChunkingService(
            chunk_size=request.chunk_size,
            overlap=request.chunk_overlap,
        )
        chunks = chunking_service.chunk_documents(documents)

        # 3. Embeddings
        embedding_service = EmbeddingService(
            client=self.embedding_client,
            model=request.embedding_model,
        )
        chunks_with_embeddings = embedding_service.embed_chunks(chunks)

        # 4. Persistência
        self.document_repo.save_batch(documents)
        self.chunk_repo.save_batch(chunks_with_embeddings)

        # Atualizar status
        for doc in documents:
            doc.mark_as_completed()
        self.document_repo.save_batch(documents)

        return IngestResultDTO(
            documents_count=len(documents),
            chunks_count=len(chunks),
            processed_document_ids=[str(doc.doc_id) for doc in documents],
        )

    def _load_documents(self, docs_dir: Path) -> List[Document]:
        """Carrega arquivos .txt do diretório."""
        documents: List[Document] = []

        if not docs_dir.exists():
            return documents

        for txt_file in docs_dir.glob("*.txt"):
            content = txt_file.read_text(encoding="utf-8")
            doc = Document.create(
                file_name=txt_file.name,
                source_path=txt_file,
                content=content,
            )
            documents.append(doc)

        return documents
