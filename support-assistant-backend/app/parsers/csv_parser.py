import csv
import io

from app.exceptions.errors import ParserError
from app.models.document import ParseContext, ParsedDocument
from app.parsers.base import DocumentParser, decode_text, parsed, with_file_classification


class CSVParser(DocumentParser):
    def supports(self, file_name: str, content_type: str | None) -> bool:
        return file_name.lower().endswith(".csv") or content_type in {"text/csv", "application/csv"}

    def parse(self, source: bytes, context: ParseContext) -> list[ParsedDocument]:
        context = with_file_classification(context, "csv")
        reader = csv.DictReader(io.StringIO(decode_text(source)))
        if not reader.fieldnames:
            raise ParserError("CSV requires a header row")
        documents = []
        for index, row in enumerate(reader, 1):
            body = "\n".join(f"{key.upper().replace('_', ' ')}:\n{value}" for key, value in row.items() if value)
            row_context = context.model_copy(update={"document_id": f"{context.document_id}-{index}"})
            documents.append(parsed(row_context, row.get("title") or row.get("ticket_id") or f"{context.file_name} row {index}", body, row))
        return documents
