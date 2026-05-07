from __future__ import annotations

import json
import os
import time
from pathlib import Path

from redis import Redis

from app.core.config import settings
from app.repositories.doc_repo import DocumentRepository
from app.services.chunker import TextChunker
from app.services.embedder import EmbeddingService, OpenAIEmbeddingClient
from app.services.loader import parse_txt_documents
from app.services.vector_store import FaissVectorStore


def run_worker() -> None:
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    queue_name = os.getenv("INGEST_QUEUE", "ingest:jobs")
    poll_seconds = int(os.getenv("WORKER_POLL_SECONDS", "2"))

    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is required for worker execution")

    redis_client = Redis.from_url(redis_url, decode_responses=True)
    vector_store = FaissVectorStore()
    document_repo = DocumentRepository()

    while True:
        job = redis_client.lpop(queue_name)
        if job is None:
            time.sleep(poll_seconds)
            continue

        payload = json.loads(job)
        docs_dir = Path(payload.get("docs_dir", str(settings.docs_dir)))
        chunk_size = int(payload.get("chunk_size", settings.chunk_size))
        chunk_overlap = int(payload.get("chunk_overlap", settings.chunk_overlap))
        embedding_model = payload.get("embedding_model", settings.embedding_model)

        parsed_documents = parse_txt_documents(docs_dir=docs_dir)
        chunker = TextChunker(chunk_size=chunk_size, overlap=chunk_overlap)
        chunks = chunker.chunk_documents(parsed_documents)

        embed_client = OpenAIEmbeddingClient(api_key=settings.openai_api_key)
        embedder = EmbeddingService(client=embed_client, model=embedding_model)
        embedded_chunks = embedder.embed_chunks(chunks)

        vector_store.add_embeddings(embedded_chunks)
        document_repo.upsert_documents(parsed_documents)


if __name__ == "__main__":
    run_worker()
