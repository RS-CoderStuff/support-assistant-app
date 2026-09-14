import json
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.error import URLError
from urllib.request import Request, urlopen

from app.aws.bedrock_client import BedrockRuntimeClient
from app.services.metadata_extractor import MetadataExtractionService
from app.services.query_classifier import QueryClassifier
from app.services.query_rewriter import QueryRewriteService
from app.services.retrieval_decision import RetrievalDecisionService
from app.utils.logging import log_event


@dataclass(frozen=True)
class SemanticUnderstanding:
    standalone_query: str
    issue_update: dict[str, str]
    topic_changed: bool
    confidence: float


@dataclass(frozen=True)
class QueryUnderstandingResult:
    query_type: str
    rewritten_query: str
    extracted_metadata: dict[str, str]
    current_issue: dict[str, str]
    retrieval_required: bool
    retrieval_basis: str
    semantic_provider: str | None


class SemanticUnderstandingProvider(Protocol):
    name: str

    def understand(self, message: str, stored_issue: dict[str, Any], request_context: dict[str, Any]) -> SemanticUnderstanding | None: ...


class OllamaSemanticUnderstandingProvider:
    name = "ollama"

    def __init__(self, base_url: str, model: str, timeout_seconds: float) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def understand(self, message: str, stored_issue: dict[str, Any], request_context: dict[str, Any]) -> SemanticUnderstanding | None:
        payload = {"model": self.model, "stream": False, "format": "json", "messages": [{"role": "system", "content": _SEMANTIC_SYSTEM_PROMPT}, {"role": "user", "content": _semantic_prompt(message, stored_issue, request_context)}], "options": {"temperature": 0, "num_predict": 300}}
        request = Request(f"{self.base_url}/api/chat", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}, method="POST")
        log_event("semantic_understanding_provider_request", provider=self.name, endpoint=f"{self.base_url}/api/chat", request_payload=payload)
        log_event("semantic_understanding_provider_started", provider=self.name, model=self.model, message_length=len(message))
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                body = json.loads(response.read().decode())
        except (OSError, URLError, json.JSONDecodeError) as error:
            log_event("semantic_understanding_provider_failed", provider=self.name, model=self.model, error_type=type(error).__name__)
            return None
        result = _parse_semantic_understanding(body.get("message", {}).get("content", ""))
        log_event("semantic_understanding_provider_completed", provider=self.name, model=self.model, response_accepted=bool(result), confidence=result.confidence if result else None)
        return result


class BedrockSemanticUnderstandingProvider:
    name = "bedrock"

    def __init__(self, client: BedrockRuntimeClient, model_id: str, timeout_seconds: float) -> None:
        self.client = client
        self.model_id = model_id
        self.timeout_seconds = timeout_seconds

    def understand(self, message: str, stored_issue: dict[str, Any], request_context: dict[str, Any]) -> SemanticUnderstanding | None:
        log_event("semantic_understanding_provider_started", provider=self.name, model_id=self.model_id, message_length=len(message))
        request_payload = {"modelId": self.model_id, "messages": [{"role": "user", "content": [{"text": f"{_SEMANTIC_SYSTEM_PROMPT}\n{_semantic_prompt(message, stored_issue, request_context)}"}]}], "inferenceConfig": {"temperature": 0, "maxTokens": 300}}
        log_event("semantic_understanding_provider_request", provider=self.name, request_payload=request_payload)
        try:
            response = self.client.client.converse(**request_payload)
        except Exception as error:
            log_event("semantic_understanding_provider_failed", provider=self.name, model_id=self.model_id, error_type=type(error).__name__)
            return None
        result = _parse_semantic_understanding(response["output"]["message"]["content"][0]["text"])
        log_event("semantic_understanding_provider_completed", provider=self.name, model_id=self.model_id, response_accepted=bool(result), confidence=result.confidence if result else None, usage=response.get("usage", {}), latency_ms=response.get("metrics", {}).get("latencyMs"))
        return result


_SEMANTIC_SYSTEM_PROMPT = """Return JSON only with standalone_query, issue_update, topic_changed, and confidence.
Resolve references in the current user message using stored_issue. The standalone_query must preserve the user's intent and be understandable without conversation history.
issue_update may contain only current_issue_summary, product, component, environment, error_code, version, status, or trigger. Include facts only when explicitly present in the user message or request_context. Do not copy unverified stored facts into issue_update. Set topic_changed to true only when the user starts a distinct support issue. Confidence must be a number from 0 to 1."""
_ISSUE_FIELDS = {"current_issue_summary", "product", "component", "environment", "error_code", "version", "status", "trigger"}


def _semantic_prompt(message: str, stored_issue: dict[str, Any], request_context: dict[str, Any]) -> str:
    return json.dumps({"task": "Return standalone_query, issue_update, topic_changed, and confidence. standalone_query must resolve references in the user message. issue_update must contain only facts explicitly present in the message or request_context.", "stored_issue": stored_issue, "request_context": request_context, "user_message": message})


def _parse_semantic_understanding(content: str) -> SemanticUnderstanding | None:
    try:
        payload = json.loads(content)
        standalone_query = payload["standalone_query"].strip()
        confidence = float(payload["confidence"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None
    issue_update = {key: str(value) for key, value in payload.get("issue_update", {}).items() if key in _ISSUE_FIELDS and value}
    if not standalone_query or not 0 <= confidence <= 1:
        return None
    return SemanticUnderstanding(standalone_query, issue_update, bool(payload.get("topic_changed", False)), confidence)


class QueryUnderstandingService:
    def __init__(self, classifier: QueryClassifier, rewriter: QueryRewriteService, extractor: MetadataExtractionService, decision: RetrievalDecisionService, local_provider: SemanticUnderstandingProvider | None = None, cloud_provider: SemanticUnderstandingProvider | None = None, minimum_confidence: float = 0.8) -> None:
        self.classifier = classifier
        self.rewriter = rewriter
        self.extractor = extractor
        self.decision = decision
        self.local_provider = local_provider
        self.cloud_provider = cloud_provider
        self.minimum_confidence = minimum_confidence

    def understand(self, message: str, stored_issue: dict[str, Any], request_context: dict[str, Any], active_evidence: list[dict[str, Any]], request_id: str | None = None, conversation_id: str | None = None) -> QueryUnderstandingResult:
        log_event("query_understanding_started", request_id=request_id, conversation_id=conversation_id, message_length=len(message), stored_issue_keys=sorted(stored_issue), request_context_keys=sorted(request_context), active_evidence_count=len(active_evidence))
        query_type = self.classifier.classify(message, bool(stored_issue))
        metadata = self.extractor.extract(message, request_context)
        rewritten_query = self.rewriter.rewrite(message, request_context or stored_issue if query_type == "FOLLOW_UP" else {})
        log_event("deterministic_query_understanding_completed", request_id=request_id, conversation_id=conversation_id, query_type=query_type, extracted_metadata_keys=sorted(metadata), rewritten_query_changed=rewritten_query != message)
        semantic, semantic_provider = self._semantic_understanding(message, stored_issue, request_context, query_type, metadata, request_id, conversation_id)
        if semantic:
            rewritten_query = semantic.standalone_query
            metadata = {**metadata, **semantic.issue_update}
            if semantic.topic_changed:
                query_type = "NEW_ISSUE"
            log_event("semantic_understanding_applied", request_id=request_id, conversation_id=conversation_id, provider=semantic_provider, confidence=semantic.confidence, topic_changed=semantic.topic_changed, issue_update_keys=sorted(semantic.issue_update), rewritten_query_changed=rewritten_query != message)
        current_issue = self._current_issue(query_type, message, stored_issue, request_context, metadata)
        retrieval_required, retrieval_basis = self.decision.decide(query_type, active_evidence, message)
        log_event("query_understanding_completed", request_id=request_id, conversation_id=conversation_id, query_type=query_type, semantic_provider=semantic_provider, current_issue_keys=sorted(current_issue), extracted_metadata_keys=sorted(metadata), retrieval_required=retrieval_required, retrieval_basis=retrieval_basis)
        return QueryUnderstandingResult(query_type, rewritten_query, metadata, current_issue, retrieval_required, retrieval_basis, semantic_provider)

    def _semantic_understanding(self, message: str, stored_issue: dict[str, Any], request_context: dict[str, Any], query_type: str, metadata: dict[str, str], request_id: str | None, conversation_id: str | None) -> tuple[SemanticUnderstanding | None, str | None]:
        if not self._needs_semantic_understanding(message, query_type, stored_issue, metadata):
            log_event("semantic_understanding_skipped", request_id=request_id, conversation_id=conversation_id, reason="deterministic_understanding_sufficient")
            return None, None
        log_event("semantic_understanding_started", request_id=request_id, conversation_id=conversation_id, query_type=query_type, local_provider_configured=bool(self.local_provider), cloud_provider_configured=bool(self.cloud_provider))
        for provider in (self.local_provider, self.cloud_provider):
            if not provider:
                continue
            log_event("semantic_understanding_provider_attempted", request_id=request_id, conversation_id=conversation_id, provider=provider.name)
            result = provider.understand(message, stored_issue, request_context)
            if result and result.confidence >= self.minimum_confidence:
                log_event("semantic_understanding_provider_accepted", request_id=request_id, conversation_id=conversation_id, provider=provider.name, confidence=result.confidence)
                return result, provider.name
            log_event("semantic_understanding_provider_rejected", request_id=request_id, conversation_id=conversation_id, provider=provider.name, reason="no_valid_result" if not result else "confidence_below_threshold", confidence=result.confidence if result else None, minimum_confidence=self.minimum_confidence)
        log_event("semantic_understanding_unavailable", request_id=request_id, conversation_id=conversation_id, reason="no_provider_returned_an_acceptable_result")
        return None, None

    @staticmethod
    def _needs_semantic_understanding(message: str, query_type: str, stored_issue: dict[str, Any], metadata: dict[str, str]) -> bool:
        if query_type in {"GREETING", "CLARIFICATION"}:
            return False
        if query_type == "SUMMARY_REQUEST":
            return True
        if query_type == "FOLLOW_UP":
            return True
        return query_type in {"NEW_ISSUE", "KNOWLEDGE_QUERY"} and not metadata

    @staticmethod
    def _current_issue(query_type: str, message: str, stored_issue: dict[str, Any], request_context: dict[str, Any], metadata: dict[str, str]) -> dict[str, str]:
        if query_type == "NEW_ISSUE":
            return {"issue_summary": message, **metadata}
        if request_context:
            return metadata
        if query_type == "FOLLOW_UP":
            return {**stored_issue, **metadata}
        return {key: str(value) for key, value in stored_issue.items()}