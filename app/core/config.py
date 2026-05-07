from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True, slots=True)
class RagSettings:
    docs_dir: Path = Path("data/docs")
    faiss_dir: Path = Path("data/faiss")
    faiss_index_file: str = "index.faiss"
    faiss_metadata_file: str = "chunks_metadata.json"
    documents_metadata_file: str = "documents_metadata.json"
    chunk_size: int = 600
    chunk_overlap: int = 100
    embedding_model: str = "text-embedding-3-small"
    openai_api_key: str = ""


settings = RagSettings(
    docs_dir=Path(os.getenv("DOCS_DIR", "data/docs")),
    faiss_dir=Path(os.getenv("FAISS_DIR", "data/faiss")),
    chunk_size=int(os.getenv("CHUNK_SIZE", "600")),
    chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "100")),
    embedding_model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
    openai_api_key=os.getenv("OPENAI_API_KEY", ""),
)
