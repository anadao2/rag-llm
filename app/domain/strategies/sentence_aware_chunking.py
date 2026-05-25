from __future__ import annotations

import re
from typing import List

from app.domain.entities.chunk import Chunk
from app.domain.entities.document import Document
from app.domain.strategies.chunking_strategy import ChunkingStrategy, ChunkingConfig


class SentenceAwareChunking(ChunkingStrategy):
    """
    Estratégia de chunking que respeita limites de sentença.
    Implementação concreta do Strategy Pattern (OCP).
    """

    _SENTENCE_END = re.compile(r"[.!?] +")
    _WHITESPACE = re.compile(r"\s+")

    def chunk(self, document: Document, config: ChunkingConfig) -> List[Chunk]:
        if not document.content:
            return []

        # Normalizar
        text = self._normalize(document.content)
        if not text:
            return []

        chunks: List[Chunk] = []
        start = 0
        order = 0
        text_len = len(text)

        while start < text_len:
            # Calcular fim ideal
            ideal_end = min(start + config.chunk_size, text_len)
            
            if config.respect_boundaries and ideal_end < text_len:
                ideal_end = self._find_boundary(text, start, ideal_end)

            chunk_text = text[start:ideal_end].strip()
            if chunk_text:
                chunk = Chunk.create(
                    doc_id=document.doc_id,
                    text=chunk_text,
                    order=order,
                    start_char=start,
                    end_char=ideal_end,
                    file_name=document.file_name,
                    source_path=str(document.source_path),
                )
                chunks.append(chunk)
                order += 1

            if ideal_end >= text_len:
                break
                
            start = max(0, ideal_end - config.overlap)

        return chunks

    def _normalize(self, text: str) -> str:
        """Remove espaços excessivos."""
        return self._WHITESPACE.sub(" ", text).strip()

    def _find_boundary(self, text: str, start: int, end: int) -> int:
        """
        Encontra melhor limite (sentença ou espaço).
        Mantém coerência semântica.
        """
        window = text[start:end]
        
        # Preferir fim de sentença
        for match in self._SENTENCE_END.finditer(window):
            if match.end() > len(window) * 0.5:  # Pelo menos metade do chunk
                return start + match.end()
        
        # Fallback: quebra em espaço
        last_space = window.rfind(" ")
        if last_space > len(window) * 0.5:
            return start + last_space
        
        return end

    def get_name(self) -> str:
        return "sentence-aware"
