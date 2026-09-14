from typing import Any

from app.models.document import ParsedDocument


class MetadataEnricher:
    allowed_keys = {"ticket_id", "source_type", "document_type", "product", "component", "type", "subtype", "environment", "severity", "team", "resolution_verified", "resolution_quality", "document_version", "effective_date", "status", "access_level"}

    def enrich(self, document: ParsedDocument, provided: dict[str, Any]) -> dict[str, Any]:
        deterministic = {"source_type": document.source_type, "document_type": document.document_type, "file_type": document.original_file_name.rsplit(".", 1)[-1].lower()}
        merged = {**deterministic, **document.extracted_metadata, **provided}
        return {key: value for key, value in merged.items() if key in self.allowed_keys or key == "file_type" and value is not None}


class BedrockMetadataSerializer:
    def serialize(self, metadata: dict[str, Any]) -> dict[str, Any]:
        return {"metadataAttributes": metadata}
