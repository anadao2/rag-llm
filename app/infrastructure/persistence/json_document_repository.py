from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List

from app.domain.entities.document import Document
from app.domain.repositories.document_repository import DocumentRepository
from app.domain.value_objects.document_id import DocumentId
from app.infrastructure.persistence.mappers.document_mapper import DocumentMapper


class JsonDocumentRepository(DocumentRepository):
    """
    Adapter - Implementação concreta usando JSON files.
    Faz a tradução entre o modelo de domínio e o modelo de persistência.
    """

    def __init__(
        self,
        base_dir: Path,
        metadata_file: str = "documents_metadata.json",
    ) -> None:
        self.base_dir = Path(base_dir)
        self.file_path = self.base_dir / metadata_file
        self._mapper = DocumentMapper()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save(self, document: Document) -> None:
        data = self._load_data()
        record = self._mapper.to_record(document)
        data[record["doc_id"]] = record
        self._save_data(data)

    def save_batch(self, documents: List[Document]) -> None:
        data = self._load_data()
        for doc in documents:
            record = self._mapper.to_record(doc)
            data[record["doc_id"]] = record
        self._save_data(data)

    def find_by_id(self, doc_id: DocumentId) -> Document | None:
        data = self._load_data()
        record = data.get(str(doc_id))
        if record:
            return self._mapper.to_domain(record)
        return None

    def find_all(self) -> List[Document]:
        data = self._load_data()
        return [self._mapper.to_domain(record) for record in data.values()]

    def count(self) -> int:
        return len(self._load_data())

    def exists(self, doc_id: DocumentId) -> bool:
        return str(doc_id) in self._load_data()

    def _load_data(self) -> dict[str, Any]:
        if not self.file_path.exists():
            return {}
        content = self.file_path.read_text(encoding="utf-8")
        return json.loads(content)

    def _save_data(self, data: dict[str, Any]) -> None:
        self.file_path.write_text(
            json.dumps(data, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )
