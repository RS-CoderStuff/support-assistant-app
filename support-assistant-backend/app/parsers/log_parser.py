import re

from app.models.document import ParseContext, ParsedDocument
from app.parsers.base import DocumentParser, decode_text, parsed, with_file_classification


class LogParser(DocumentParser):
    pattern = re.compile(r"(?P<timestamp>\d{4}-\d{2}-\d{2}[T ][^\s]+)?\s*(?:\[(?P<level>DEBUG|INFO|WARN|WARNING|ERROR|FATAL)\]|(?P<level2>DEBUG|INFO|WARN|WARNING|ERROR|FATAL))?\s*(?P<message>.*)", re.I)

    def supports(self, file_name: str, content_type: str | None) -> bool:
        return file_name.lower().endswith((".log", ".out")) or content_type in {"text/x-log", "application/log"}

    def parse(self, source: bytes, context: ParseContext) -> list[ParsedDocument]:
        context = with_file_classification(context, "log")
        lines = decode_text(source).splitlines()
        errors = [index for index, line in enumerate(lines) if re.search(r"\b(ERROR|FATAL|Exception)\b", line, re.I)]
        if not errors:
            return [parsed(context, context.file_name, "\n".join(lines), {"log_level": "UNKNOWN"})]
        documents = []
        for sequence, error_index in enumerate(errors, 1):
            start, end = max(0, error_index - 10), min(len(lines), error_index + 40)
            match = self.pattern.match(lines[error_index])
            metadata = {"log_level": (match.group("level") or match.group("level2") or "ERROR").upper() if match else "ERROR"}
            error_context = context.model_copy(update={"document_id": f"{context.document_id}-{sequence}"})
            documents.append(parsed(error_context, f"{context.file_name} diagnostic {sequence}", "\n".join(lines[start:end]), metadata))
        return documents
