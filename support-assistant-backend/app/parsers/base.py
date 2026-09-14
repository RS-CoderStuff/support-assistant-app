from abc import ABC, abstractmethod

from app.models.document import ParseContext, ParsedDocument


class DocumentParser(ABC):
    @abstractmethod
    def supports(self, file_name: str, content_type: str | None) -> bool: ...

    @abstractmethod
    def parse(self, source: bytes, context: ParseContext) -> list[ParsedDocument]: ...


def decode_text(source: bytes) -> str:
    return source.decode("utf-8", errors="replace")


def with_file_classification(context: ParseContext, file_type: str) -> ParseContext:
    return context.model_copy(
        update={
            "source_type": "uploaded_document" if context.source_type == "unknown" else context.source_type,
            "document_type": file_type if context.document_type == "document" else context.document_type,
        }
    )


def parsed(context: ParseContext, title: str, content: str, metadata: dict | None = None) -> ParsedDocument:
    return ParsedDocument(
        document_id=context.document_id,
        title=title or context.file_name,
        content=content,
        source_type=context.source_type,
        document_type=context.document_type,
        source_uri=context.source_uri,
        original_file_name=context.file_name,
        content_type=context.content_type,
        extracted_metadata=metadata or {},
    )
