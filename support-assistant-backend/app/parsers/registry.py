from app.exceptions.errors import UnsupportedFileTypeError
from app.models.document import ParseContext, ParsedDocument
from app.parsers.base import DocumentParser


class ParserRegistry:
    def __init__(self, parsers: list[DocumentParser]) -> None:
        self.parsers = parsers

    def parse(self, source: bytes, context: ParseContext) -> list[ParsedDocument]:
        for parser in self.parsers:
            if parser.supports(context.file_name, context.content_type):
                return parser.parse(source, context)
        raise UnsupportedFileTypeError(f"Unsupported file type: {context.file_name}")
