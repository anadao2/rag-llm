from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from app.domain.entities.chunk import Chunk
from app.domain.value_objects.embedding import Embedding


class EmbeddingClient(ABC):
    """
    Interface para clientes de embedding (OpenAI, local, etc).
    Domain não conhece implementações específicas.
    """

    @abstractmethod
    def embed(self, texts: List[str], model: str) -> List[List[float]]:
        """Retorna vetores de embedding para textos."""
        ...


class EmbeddingService:
    """
    Domain Service para geração de embeddings.
    Orquestra a criação de embeddings mantendo o domínio puro.
    """

    def __init__(
        self,
        client: EmbeddingClient,
        model: str,
        batch_size: int = 64,
    ) -> None:
        self.client = client
        self.model = model
        self.batch_size = batch_size

    def embed_chunks(self, chunks: List[Chunk]) -> List[Chunk]:
        """
        Gera embeddings para chunks e os anexa.
        Retorna os mesmos chunks modificados (com embedding).
        """
        if not chunks:
            return chunks

        for i in range(0, len(chunks), self.batch_size):
            batch = chunks[i : i + self.batch_size]
            texts = [chunk.text for chunk in batch]
            vectors = self.client.embed(texts, self.model)

            for chunk, vector in zip(batch, vectors):
                embedding = Embedding.from_list(vector, self.model)
                chunk.attach_embedding(embedding)

        return chunks
