from __future__ import annotations

from pathlib import Path

from app.schemas.documents import EmbeddedChunk
from app.services.chunker import TextChunker
from app.services.embedder import EmbeddingService, OpenAIEmbeddingClient
from app.services.loader import parse_txt_documents


def build_embeddings_from_txt(
    docs_dir: Path | str,
    openai_api_key: str,
    chunk_size: int = 600,
    overlap: int = 100,
    model: str = "text-embedding-3-small",
) -> list[EmbeddedChunk]:
    """
    End-to-end ingestion helper:
    parse TXT -> chunk -> embed.
    Output can be consumed directly by a FAISS adapter.
    """
    parsed_docs = parse_txt_documents(docs_dir=docs_dir)
    chunker = TextChunker(chunk_size=chunk_size, overlap=overlap)
    chunks = chunker.chunk_documents(parsed_docs)

    embed_client = OpenAIEmbeddingClient(api_key=openai_api_key)
    embedder = EmbeddingService(client=embed_client, model=model)
    return embedder.embed_chunks(chunks)
