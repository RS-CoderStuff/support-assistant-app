from typing import Any, TypedDict


class AssistantState(TypedDict, total=False):
    request_id: str
    conversation: Any
    conversation_id: str
    user_id: str
    user_message: str
    context: dict[str, Any]
    conversation_summary: str
    recent_messages: list[dict[str, Any]]
    current_issue: dict[str, Any]
    active_evidence: list[dict[str, Any]]
    query_type: str
    rewritten_query: str
    extracted_metadata: dict[str, Any]
    metadata_filter: dict[str, Any]
    retrieval_required: bool
    retrieved_documents: list[Any]
    reranked_documents: list[Any]
    validated_evidence: list[Any]
    answer: str
    confidence: float
    citations: list[dict[str, Any]]
    guardrail_result: dict[str, Any]
    retrieval_attempt: int
    errors: list[str]
