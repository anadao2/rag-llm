from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.repositories.doc_repo import DocumentRepository
from app.schemas.api import HealthResponse, IngestRequest, IngestResponse
from app.services.chunker import TextChunker
from app.services.embedder import EmbeddingService, OpenAIEmbeddingClient
from app.services.loader import parse_txt_documents
from app.services.vector_store import FaissVectorStore

router = APIRouter(tags=["ingest"])
vector_store = FaissVectorStore()
document_repo = DocumentRepository()


@router.post("/ingest", response_model=IngestResponse)
def ingest_documents(payload: IngestRequest | None = None) -> IngestResponse:
    body = payload or IngestRequest()
    docs_dir = Path(body.docs_dir) if body.docs_dir else settings.docs_dir
    chunk_size = body.chunk_size or settings.chunk_size
    chunk_overlap = body.chunk_overlap if body.chunk_overlap is not None else settings.chunk_overlap
    embedding_model = body.embedding_model or settings.embedding_model

    if chunk_overlap >= chunk_size:
        raise HTTPException(status_code=400, detail="chunk_overlap must be lower than chunk_size")
    if not settings.openai_api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured")

    parsed_documents = parse_txt_documents(docs_dir=docs_dir)
    chunker = TextChunker(chunk_size=chunk_size, overlap=chunk_overlap)
    chunks = chunker.chunk_documents(parsed_documents)

    embed_client = OpenAIEmbeddingClient(api_key=settings.openai_api_key)
    embedder = EmbeddingService(client=embed_client, model=embedding_model)
    embedded_chunks = embedder.embed_chunks(chunks)

    vector_store.add_embeddings(embedded_chunks)
    document_repo.upsert_documents(parsed_documents)

    return IngestResponse(documents_count=len(parsed_documents), chunks_count=len(embedded_chunks))


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    vector_health = vector_store.health()
    vector_status = "ok" if vector_health["ready"] else "empty"

    return HealthResponse(
        api_status="ok",
        vector_store_status=vector_status,
        indexed_documents_count=document_repo.count(),
    )
