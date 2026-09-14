import re

from app.models.document import KnowledgeChunk


class Chunker:
    def __init__(self, chunk_size: int = 1600, overlap: int = 200) -> None:
        if overlap >= chunk_size:
            raise ValueError("overlap must be smaller than chunk_size")
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, document_id: str, content: str, metadata: dict) -> list[KnowledgeChunk]:
        sections = [section.strip() for section in re.split(r"\n\s*\n", content) if section.strip()]
        pieces: list[str] = []
        current = ""
        for section in sections:
            if current and len(current) + len(section) + 2 > self.chunk_size:
                pieces.append(current)
                current = current[-self.overlap:] + "\n\n" + section if self.overlap else section
            else:
                current = f"{current}\n\n{section}".strip()
        if current:
            pieces.append(current)
        return [KnowledgeChunk(document_id=document_id, sequence=index, content=piece, metadata={**metadata, "document_id": document_id, "sequence": index}) for index, piece in enumerate(pieces, 1)]
