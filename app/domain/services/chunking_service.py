from __future__ import annotations

import re
from typing import List

from app.domain.entities.chunk import Chunk
from app.domain.entities.document import Document


class ChunkingService:
    """
    Domain Service para chunking de documentos.
    Regras de negócio: limites de tamanho, sobreposição, quebra em sentenças.
    """

    _MULTISPACE_RE = re.compile(r"\s+")

    def __init__(self, chunk_size: int = 600, overlap: int = 100) -> None:
        if overlap >= chunk_size:
            raise ValueError("overlap must be lower than chunk_size")
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_document(self, document: Document) -> List[Chunk]:
        """Divide documento em chunks respeitando limites semânticos."""
        normalized = self._normalize_text(document.content)
        if not normalized:
            return []

        chunks: List[Chunk] = []
        start = 0
        order = 0
        text_len = len(normalized)

        while start < text_len:
            end = min(start + self.chunk_size, text_len)
            if end < text_len:
                end = self._adjust_end(normalized, start, end)

            chunk_text = normalized[start:end].strip()
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
            start = max(0, end - self.overlap)

        return chunks

    def chunk_documents(self, documents: List[Document]) -> List[Chunk]:
        """Processa múltiplos documentos."""
        all_chunks: List[Chunk] = []
        for doc in documents:
            all_chunks.extend(self.chunk_document(doc))
        return all_chunks

    @staticmethod
    def _normalize_text(text: str) -> str:
        # Compress repeated whitespace to reduce embedding token waste.
        return ChunkingService._MULTISPACE_RE.sub(" ", text).strip()

    @staticmethod
    def _adjust_end(text: str, start: int, end: int) -> int:
        """
        Prefer sentence boundaries, fallback to whitespace boundary.
        This keeps semantic coherence without increasing chunk length.
        """
        window = text[start:end]
        sentence_break = max(window.rfind(". "), window.rfind("! "), window.rfind("? "))
        if sentence_break > int(len(window) * 0.6):
            return start + sentence_break + 1

        whitespace_break = window.rfind(" ")
        if whitespace_break > int(len(window) * 0.5):
            return start + whitespace_break

        return end
