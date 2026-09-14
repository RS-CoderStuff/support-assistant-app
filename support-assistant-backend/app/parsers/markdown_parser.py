import re

from app.models.document import ParseContext, ParsedDocument
from app.parsers.base import DocumentParser, decode_text, parsed, with_file_classification


class MarkdownParser(DocumentParser):
    def supports(self, file_name: str, content_type: str | None) -> bool:
        return file_name.lower().endswith((".md", ".markdown")) or content_type == "text/markdown"

    def parse(self, source: bytes, context: ParseContext) -> list[ParsedDocument]:
        context = with_file_classification(context, "markdown")
        content = decode_text(source)
        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        return [parsed(context, title_match.group(1).strip() if title_match else context.file_name, content)]
