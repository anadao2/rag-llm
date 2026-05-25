from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from app.domain.value_objects.document_id import DocumentId


@dataclass
class Document:
    """
    Entidade Document - identidade única baseada em doc_id.
    Pode ter seu estado alterado (metadata, processing_status).
    """

    doc_id: DocumentId
    file_name: str
    source_path: Path
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    processed_at: datetime | None = None
    status: str = "pending"  # pending, processing, completed, failed

    def __post_init__(self) -> None:
        if not self.file_name:
            raise ValueError("file_name is required")
        if not self.content:
            raise ValueError("content cannot be empty")

    @classmethod
    def create(
        cls,
        file_name: str,
        source_path: Path,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> Document:
        """Factory method para criar novo documento."""
        return cls(
            doc_id=DocumentId.generate(),
            file_name=file_name,
            source_path=source_path,
            content=content,
            metadata=metadata or {},
        )

    def mark_as_processing(self) -> None:
        self.status = "processing"

    def mark_as_completed(self) -> None:
        self.status = "completed"
        self.processed_at = datetime.utcnow()

    def mark_as_failed(self, error_message: str) -> None:
        self.status = "failed"
        self.metadata["error"] = error_message

    def update_metadata(self, key: str, value: Any) -> None:
        self.metadata[key] = value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Document):
            return False
        return self.doc_id == other.doc_id

    def __hash__(self) -> int:
        return hash(self.doc_id)
