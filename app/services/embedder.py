from __future__ import annotations

from typing import Iterable, Protocol

from app.schemas.documents import ChunkedDocument, EmbeddedChunk


class EmbeddingClient(Protocol):
    """Protocol for any embedding backend (OpenAI, mocks, local models)."""

    def embed(self, texts: list[str], model: str) -> list[list[float]]:
        ...


class OpenAIEmbeddingClient:
    """Adapter around OpenAI embeddings API."""

    def __init__(self, api_key: str) -> None:
        from openai import OpenAI

        self._client = OpenAI(api_key=api_key)

    def embed(self, texts: list[str], model: str) -> list[list[float]]:
        response = self._client.embeddings.create(model=model, input=texts)
        return [item.embedding for item in response.data]


class EmbeddingService:
    """Reusable embedding service with low coupling to provider implementation."""

    def __init__(
        self,
        client: EmbeddingClient,
        model: str = "text-embedding-3-small",
        batch_size: int = 64,
    ) -> None:
        self.client = client
        self.model = model
        self.batch_size = batch_size

    def embed_chunks(self, chunks: Iterable[ChunkedDocument]) -> list[EmbeddedChunk]:
        chunk_list = list(chunks)
        if not chunk_list:
            return []

        embedded: list[EmbeddedChunk] = []
        for start in range(0, len(chunk_list), self.batch_size):
            batch = chunk_list[start : start + self.batch_size]
            vectors = self.client.embed([chunk.text for chunk in batch], model=self.model)
            embedded.extend(self._merge_batch(batch, vectors))
        return embedded

    @staticmethod
    def _merge_batch(batch: list[ChunkedDocument], vectors: list[list[float]]) -> list[EmbeddedChunk]:
        if len(batch) != len(vectors):
            raise ValueError("embedding response size mismatch")

        result: list[EmbeddedChunk] = []
        for chunk, vector in zip(batch, vectors, strict=True):
            result.append(
                EmbeddedChunk(
                    chunk_id=chunk.chunk_id,
                    doc_id=chunk.doc_id,
                    text=chunk.text,
                    embedding=vector,
                    metadata=chunk.metadata,
                )
            )
        return result
