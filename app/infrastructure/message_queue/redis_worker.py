from __future__ import annotations

import json
import os
import time
from pathlib import Path

from redis import Redis

from app.application.dto.ingest_dto import IngestRequestDTO
from app.application.use_cases.ingest_documents import IngestDocumentsUseCase
from app.core.config import settings
from app.infrastructure.external.openai_embedder import OpenAIEmbedder
from app.infrastructure.persistence.faiss_chunk_repository import FaissChunkRepository
from app.infrastructure.persistence.json_document_repository import JsonDocumentRepository


def create_ingest_use_case() -> IngestDocumentsUseCase:
    """Factory para criar use case com dependências."""
    doc_repo = JsonDocumentRepository(base_dir=settings.faiss_dir)
    chunk_repo = FaissChunkRepository(base_dir=settings.faiss_dir)
    embedder = OpenAIEmbedder(api_key=settings.openai_api_key)

    return IngestDocumentsUseCase(
        document_repo=doc_repo,
        chunk_repo=chunk_repo,
        embedding_client=embedder,
    )


def run_worker() -> None:
    """Worker assíncrono que processa jobs da fila Redis."""
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    queue_name = os.getenv("INGEST_QUEUE", "ingest:jobs")
    poll_seconds = int(os.getenv("WORKER_POLL_SECONDS", "2"))

    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is required for worker execution")

    redis_client = Redis.from_url(redis_url, decode_responses=True)

    print(f"Worker started. Listening on queue: {queue_name}")

    while True:
        job = redis_client.lpop(queue_name)
        if job is None:
            time.sleep(poll_seconds)
            continue

        try:
            payload = json.loads(job)
            request_dto = IngestRequestDTO(
                docs_dir=Path(payload.get("docs_dir", str(settings.docs_dir))),
                chunk_size=int(payload.get("chunk_size", settings.chunk_size)),
                chunk_overlap=int(payload.get("chunk_overlap", settings.chunk_overlap)),
                embedding_model=payload.get("embedding_model", settings.embedding_model),
            )

            use_case = create_ingest_use_case()
            result = use_case.execute(request_dto)

            print(f"Processed job: {result.documents_count} docs, {result.chunks_count} chunks")

        except Exception as e:
            print(f"Error processing job: {e}")
            # Aqui poderia enviar para DLQ (Dead Letter Queue)


if __name__ == "__main__":
    run_worker()
