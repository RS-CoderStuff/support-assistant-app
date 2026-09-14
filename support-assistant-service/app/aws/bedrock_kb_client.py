from typing import Any

import boto3

from app.config.settings import Settings
from app.exceptions.exceptions import KnowledgeBaseRetrievalException
from app.models.retrieval import RetrievedDocument
from app.utils.logging import log_event, log_exception


class BedrockKnowledgeBaseClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = boto3.client("bedrock-agent-runtime", region_name=settings.aws_region)

    def retrieve(self, query: str, metadata_filter: dict[str, Any], top_k: int, request_id: str | None = None, conversation_id: str | None = None) -> list[RetrievedDocument]:
        if not self.settings.knowledge_base_id:
            log_event("knowledge_base_retrieval_skipped", request_id=request_id, conversation_id=conversation_id, reason="knowledge_base_id_not_configured")
            return []
        configuration = self._build_retrieval_configuration(metadata_filter, top_k)
        request_payload = {"knowledgeBaseId": self.settings.knowledge_base_id, "retrievalQuery": {"text": query}, "retrievalConfiguration": configuration}
        try:
            log_event("knowledge_base_retrieval_request", request_id=request_id, conversation_id=conversation_id, request_payload=request_payload)
            response = self.client.retrieve(**request_payload)
        except Exception as error:
            log_exception("knowledge_base_retrieval_failed", request_id=request_id, conversation_id=conversation_id, knowledge_base_id=self.settings.knowledge_base_id, error_type=type(error).__name__, error_message=str(error))
            raise KnowledgeBaseRetrievalException() from error
        documents = [self._normalize(item) for item in response.get("retrievalResults", [])]
        log_event("knowledge_base_retrieval_completed", request_id=request_id, conversation_id=conversation_id, knowledge_base_id=self.settings.knowledge_base_id, documents_retrieved=len(documents))
        return documents

    def _normalize(self, item: dict[str, Any]) -> RetrievedDocument:
        metadata = item.get("metadata", {})
        location = item.get("location", {}).get("s3Location", {}).get("uri", "")
        source_id = str(metadata.get("ticket_id") or metadata.get("document_id") or location)
        return RetrievedDocument(source_id=source_id, chunk_id=str(metadata.get("chunk_id", location)), source_type=str(metadata.get("source_type", "product_document")), title=metadata.get("title"), content=item.get("content", {}).get("text", ""), metadata=metadata, retrieval_score=float(item.get("score", 0)))

    def _build_retrieval_configuration(self, metadata_filter: dict[str, Any], top_k: int) -> dict[str, Any]:
        configuration_name = "managedSearchConfiguration" if self.settings.knowledge_base_retrieval_mode == "managed" else "vectorSearchConfiguration"
        search_configuration: dict[str, Any] = {"numberOfResults": top_k}
        if metadata_filter:
            search_configuration["filter"] = metadata_filter
        return {configuration_name: search_configuration}
