from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DocumentId:
    """Identificador tipado para Document."""

    value: str

    def __post_init__(self) -> None:
        if not self.value or not isinstance(self.value, str):
            raise ValueError("DocumentId must be a non-empty string")

    @classmethod
    def generate(cls) -> DocumentId:
        return cls(value=str(uuid.uuid4()))

    @classmethod
    def from_string(cls, value: str) -> DocumentId:
        return cls(value=value)

    def __str__(self) -> str:
        return self.value
