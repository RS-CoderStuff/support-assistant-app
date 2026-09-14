from app.models.retrieval import RankedDocument, RetrievedDocument


class Reranker:
    def __init__(self, enabled: bool, top_k: int) -> None:
        self.enabled = enabled
        self.top_k = top_k

    def rank(self, query: str, documents: list[RetrievedDocument]) -> list[RankedDocument]:
        ranked = [RankedDocument(document.source_id, document.chunk_id, document.source_type, document.title, document.content, document.metadata, document.retrieval_score) for document in documents]
        return sorted(ranked, key=lambda document: document.score, reverse=True)[:self.top_k]
