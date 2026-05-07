from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.schemas.documents import ParsedDocument


class DocumentRepository:
    """Stores indexed document metadata for health and audits."""

    def __init__(
        self,
        base_dir: Path | str = settings.faiss_dir,
        metadata_file: str = settings.documents_metadata_file,
    ) -> None:
        self.base_dir = Path(base_dir)
        self.file_path = self.base_dir / metadata_file
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def upsert_documents(self, documents: list[ParsedDocument]) -> None:
        if not documents:
            return
        existing = {doc["doc_id"]: doc for doc in self._read()}
        for doc in documents:
            existing[doc.doc_id] = {
                "doc_id": doc.doc_id,
                "file_name": doc.file_name,
                "source_path": doc.source_path,
                "metadata": doc.metadata,
            }
        payload = list(existing.values())
        self.file_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")

    def count(self) -> int:
        return len(self._read())

    def _read(self) -> list[dict[str, Any]]:
        if not self.file_path.exists():
            return []
        return json.loads(self.file_path.read_text(encoding="utf-8"))
