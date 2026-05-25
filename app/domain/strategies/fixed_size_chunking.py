from __future__ import annotations

import re
from typing import List

from app.domain.entities.chunk import Chunk
from app.domain.entities.document import Document
from app.domain.strategies.chunking_strategy import ChunkingStrategy, ChunkingConfig


class FixedSizeChunking(ChunkingStrategy):
    """
    Estratégia de chunking com tamanho fixo.
    Implementação alternativa do Strategy Pattern (OCP).
    Simples e previsível, mas pode quebrar sentenças.
    """

    _WHITESPACE = re.compile(r"\s+")

    def chunk(self, document: Document, config: ChunkingConfig) -> List[Chunk]:
        if not document.content:
            return []

        text = self._normalize(document.content)
        if not text:
            return []

        chunks: List[Chunk] = []
        start = 0
        order = 0
        text_len = len(text)

        while start < text_len:
            end = min(start + config.chunk_size, text_len)
            
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunk = Chunk.create(
                    doc_id=document.doc_id,
                    text=chunk_text,
                    order=order,
                    start_char=start,
                    end_char=end,
                    file_name=document.file_name,
                    source_path=str(document.source_path),
                )
                chunks.append(chunk)
                order += 1

            if end >= text_len:
                break
                
            start = max(0, end - config.overlap)

        return chunks

    def _normalize(self, text: str) -> str:
        """Remove espaços excessivos."""
        return self._WHITESPACE.sub(" ", text).strip()

    def get_name(self) -> str:
        return "fixed-size"
