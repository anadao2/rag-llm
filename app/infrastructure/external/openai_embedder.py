from __future__ import annotations

from typing import List

from app.domain.services.embedding_service import EmbeddingClient


class OpenAIEmbedder(EmbeddingClient):
    """
    Adapter - Implementação concreta do EmbeddingClient usando OpenAI API.
    """

    def __init__(self, api_key: str) -> None:
        from openai import OpenAI
        self._client = OpenAI(api_key=api_key)

    def embed(self, texts: List[str], model: str) -> List[List[float]]:
        """Gera embeddings via OpenAI API."""
        response = self._client.embeddings.create(model=model, input=texts)
        return [item.embedding for item in response.data]
