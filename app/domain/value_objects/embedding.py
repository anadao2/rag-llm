from __future__ import annotations

from dataclasses import dataclass
from typing import List

import numpy as np


@dataclass(frozen=True, slots=True)
class Embedding:
    """Vetor de embedding imutável."""

    vector: tuple[float, ...]
    model: str
    dimensions: int

    def __post_init__(self) -> None:
        if len(self.vector) != self.dimensions:
            raise ValueError(f"Vector length {len(self.vector)} does not match dimensions {self.dimensions}")

    @classmethod
    def from_list(cls, vector: List[float], model: str) -> Embedding:
        return cls(
            vector=tuple(vector),
            model=model,
            dimensions=len(vector)
        )

    def to_numpy(self) -> np.ndarray:
        return np.array(self.vector, dtype=np.float32)

    def __len__(self) -> int:
        return self.dimensions
