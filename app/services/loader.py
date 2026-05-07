from __future__ import annotations

from hashlib import sha1
from pathlib import Path
from typing import Iterable

from app.schemas.documents import ParsedDocument


class TxtDocumentParser:
    """Parser focused on TXT files for RAG ingestion."""

    def __init__(self, docs_dir: Path | str = Path("data/docs"), encoding: str = "utf-8") -> None:
        self.docs_dir = Path(docs_dir)
        self.encoding = encoding

    def list_txt_files(self) -> list[Path]:
        if not self.docs_dir.exists():
            return []
        return sorted(path for path in self.docs_dir.glob("*.txt") if path.is_file())

    def parse_file(self, file_path: Path | str) -> ParsedDocument:
        path = Path(file_path)
        raw_text = path.read_text(encoding=self.encoding, errors="ignore")
        content = raw_text.strip()

        doc_id = sha1(str(path.resolve()).encode("utf-8")).hexdigest()
        metadata = {
            "extension": path.suffix.lower(),
            "size_bytes": path.stat().st_size,
            "char_count": len(content),
        }

        return ParsedDocument(
            doc_id=doc_id,
            source_path=str(path),
            file_name=path.name,
            content=content,
            metadata=metadata,
        )

    def parse_all(self) -> list[ParsedDocument]:
        return [self.parse_file(path) for path in self.list_txt_files()]


def parse_txt_documents(
    docs_dir: Path | str = Path("data/docs"),
    file_paths: Iterable[Path | str] | None = None,
) -> list[ParsedDocument]:
    """
    Parse TXT documents from a directory or explicit iterable of paths.

    This helper keeps ingestion code decoupled from parser instantiation details.
    """
    parser = TxtDocumentParser(docs_dir=docs_dir)
    if file_paths is None:
        return parser.parse_all()
    return [parser.parse_file(path) for path in file_paths]
