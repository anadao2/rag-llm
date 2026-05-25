from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from app.domain.entities.document import Document
from app.domain.value_objects.document_id import DocumentId


class DocumentMapper:
    """
    Mapper - Traduz entre Document (Domain) e dict (Persistence Model).
    Isola o domínio de mudanças no esquema de persistência.
    """

    def to_record(self, document: Document) -> Dict[str, Any]:
        """Converte Document para formato de persistência."""
        return {
            "doc_id": str(document.doc_id),
            "file_name": document.file_name,
            "source_path": str(document.source_path),
            "content": document.content,
            "metadata": document.metadata,
            "created_at": document.created_at.isoformat(),
            "processed_at": document.processed_at.isoformat() if document.processed_at else None,
            "status": document.status,
        }

    def to_domain(self, record: Dict[str, Any]) -> Document:
        """Converte registro de persistência para Document."""
        doc = Document(
            doc_id=DocumentId.from_string(record["doc_id"]),
            file_name=record["file_name"],
            source_path=Path(record["source_path"]),
            content=record["content"],
            metadata=record.get("metadata", {}),
        )
        # Restaurar timestamps e status
        if record.get("created_at"):
            doc.created_at = datetime.fromisoformat(record["created_at"])
        if record.get("processed_at"):
            doc.processed_at = datetime.fromisoformat(record["processed_at"])
        doc.status = record.get("status", "pending")
        return doc
