from app.models.document import ParseContext, ParsedDocument
from app.parsers.base import DocumentParser, decode_text, parsed, with_file_classification


class TextParser(DocumentParser):
    def supports(self, file_name: str, content_type: str | None) -> bool:
        return file_name.lower().endswith(".txt") or content_type == "text/plain"

    def parse(self, source: bytes, context: ParseContext) -> list[ParsedDocument]:
        context = with_file_classification(context, "txt")
        return [parsed(context, context.file_name, decode_text(source))]
