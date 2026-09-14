import json
from typing import Any

from app.exceptions.errors import ParserError
from app.models.document import ParseContext, ParsedDocument
from app.parsers.base import DocumentParser, decode_text, parsed, with_file_classification


class JSONParser(DocumentParser):
    ticket_fields = ("title", "description", "problem", "symptoms", "root_cause", "resolution", "verification")
    metadata_fields = ("ticket_id", "environment", "product", "component", "type", "subtype", "severity", "team", "status", "resolution_verified", "resolution_quality", "document_version", "effective_date", "access_level")

    def supports(self, file_name: str, content_type: str | None) -> bool:
        return file_name.lower().endswith(".json") or content_type == "application/json"

    def parse(self, source: bytes, context: ParseContext) -> list[ParsedDocument]:
        try:
            payload: Any = json.loads(decode_text(source))
        except json.JSONDecodeError as error:
            raise ParserError("Invalid JSON document") from error
        records = payload if isinstance(payload, list) else [payload]
        if not all(isinstance(record, dict) for record in records):
            raise ParserError("JSON root must be an object or array of objects")
        documents = []
        for index, record in enumerate(records):
            metadata = {key: record[key] for key in self.metadata_fields if record.get(key) is not None}
            sections = [f"{key.upper().replace('_', ' ')}:\n{self._text(record[key])}" for key in self.ticket_fields if record.get(key) is not None]
            if not sections:
                sections = [f"{key.upper().replace('_', ' ')}:\n{self._text(value)}" for key, value in sorted(record.items())]
            is_ticket = record.get("ticket_id") is not None
            record_context = context.model_copy(update={"document_id": context.document_id if len(records) == 1 else f"{context.document_id}-{index + 1}", "source_type": str(record.get("source_type") or ("historical_ticket" if is_ticket else context.source_type)), "document_type": str(record.get("document_type") or ("support_ticket" if is_ticket else context.document_type))})
            record_context = with_file_classification(record_context, "json")
            documents.append(parsed(record_context, str(record.get("title") or record.get("ticket_id") or context.file_name), "\n\n".join(sections), metadata))
        return documents

    @staticmethod
    def _text(value: Any) -> str:
        return json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else str(value)
