from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RetrievedDocument:
    source_id: str
    chunk_id: str
    source_type: str
    title: str | None
    content: str
    metadata: dict[str, Any]
    retrieval_score: float


@dataclass(frozen=True)
class RankedDocument:
    source_id: str
    chunk_id: str
    source_type: str
    title: str | None
    content: str
    metadata: dict[str, Any]
    score: float
