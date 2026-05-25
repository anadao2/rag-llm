from __future__ import annotations

from typing import List

from app.domain.entities.document import Document
from app.domain.specifications.specification import Specification


class DocumentProcessedSpecification(Specification[Document]):
    """
    Especificação: Documento foi processado com sucesso.
    SRP: Uma única responsabilidade - verificar status.
    """

    def is_satisfied_by(self, candidate: Document) -> bool:
        return candidate.status == "completed"


class DocumentFailedSpecification(Specification[Document]):
    """Especificação: Documento falhou no processamento."""

    def is_satisfied_by(self, candidate: Document) -> bool:
        return candidate.status == "failed"


class DocumentByFileNameSpecification(Specification[Document]):
    """Especificação: Documento com nome de arquivo específico."""

    def __init__(self, file_name: str) -> None:
        self._file_name = file_name

    def is_satisfied_by(self, candidate: Document) -> bool:
        return candidate.file_name == self._file_name


class DocumentByExtensionSpecification(Specification[Document]):
    """Especificação: Documento com extensão específica."""

    def __init__(self, extension: str) -> None:
        self._extension = extension.lower()

    def is_satisfied_by(self, candidate: Document) -> bool:
        return candidate.file_name.lower().endswith(self._extension)


class DocumentWithContentSpecification(Specification[Document]):
    """Especificação: Documento contém texto específico."""

    def __init__(self, text: str, case_sensitive: bool = False) -> None:
        self._text = text
        self._case_sensitive = case_sensitive

    def is_satisfied_by(self, candidate: Document) -> bool:
        if self._case_sensitive:
            return self._text in candidate.content
        return self._text.lower() in candidate.content.lower()


# Specifications pré-instantiadas para reuso
PROCESSED = DocumentProcessedSpecification()
FAILED = DocumentFailedSpecification()
TXT_FILES = DocumentByExtensionSpecification(".txt")
