from dataclasses import dataclass
import re

from app.models.retrieval import RankedDocument


@dataclass(frozen=True)
class EvidenceResult:
    documents: list[RankedDocument]
    conflicts: bool


class EvidenceValidator:
    def __init__(self, minimum_score: float, minimum_sources: int, final_top_k: int) -> None:
        self.minimum_score = minimum_score
        self.minimum_sources = minimum_sources
        self.final_top_k = final_top_k

    def validate(self, documents: list[RankedDocument], metadata: dict[str, str]) -> EvidenceResult:
        seen: set[tuple[str, str]] = set()
        valid: list[RankedDocument] = []
        for document in documents:
            if document.score < self.minimum_score or (document.source_id, document.chunk_id) in seen:
                continue
            if re.search(r"ignore (all|previous)|reveal (the )?system prompt", document.content, re.IGNORECASE):
                continue
            if document.metadata.get("document_status") not in (None, "active"):
                continue
            if any(document.metadata.get(key) not in (None, value) for key, value in metadata.items() if key in {"product", "component", "environment"}):
                continue
            seen.add((document.source_id, document.chunk_id))
            valid.append(document)
        return EvidenceResult(valid[:self.final_top_k], False)
