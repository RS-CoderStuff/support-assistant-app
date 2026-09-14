from app.services.metadata_extractor import MetadataExtractionService
from app.services.query_classifier import QueryClassifier
from app.services.query_rewriter import QueryRewriteService
from app.services.query_understanding import QueryUnderstandingService, SemanticUnderstanding
from app.services.retrieval_decision import RetrievalDecisionService


class StaticProvider:
    name = "local-test"

    def __init__(self, result: SemanticUnderstanding | None) -> None:
        self.result = result
        self.calls = 0

    def understand(self, message, stored_issue, request_context):
        self.calls += 1
        return self.result


def _service(provider=None) -> QueryUnderstandingService:
    return QueryUnderstandingService(QueryClassifier(), QueryRewriteService(), MetadataExtractionService(), RetrievalDecisionService(), local_provider=provider)


def test_new_issue_without_metadata_persists_summary_without_filter_data() -> None:
    result = _service().understand("Why is the Payment API down after deployment?", {}, {}, [])

    assert result.query_type == "NEW_ISSUE"
    assert result.current_issue == {"issue_summary": "Why is the Payment API down after deployment?"}


def test_semantic_provider_enriches_ambiguous_new_issue() -> None:
    provider = StaticProvider(SemanticUnderstanding("Why is the Payment API unavailable after deployment?", {"product": "payments", "component": "api"}, False, 0.95))

    result = _service(provider).understand("Why is the Payment API down after deployment?", {}, {}, [])

    assert result.rewritten_query == "Why is the Payment API unavailable after deployment?"
    assert result.current_issue["product"] == "payments"


def test_low_confidence_local_result_uses_cloud_fallback() -> None:
    local_provider = StaticProvider(SemanticUnderstanding("Local query", {}, False, 0.5))
    cloud_provider = StaticProvider(SemanticUnderstanding("Cloud query", {"product": "payments"}, False, 0.95))
    cloud_provider.name = "cloud-test"
    service = QueryUnderstandingService(QueryClassifier(), QueryRewriteService(), MetadataExtractionService(), RetrievalDecisionService(), local_provider=local_provider, cloud_provider=cloud_provider)

    result = service.understand("Why is the Payment API down after deployment?", {}, {}, [])

    assert result.rewritten_query == "Cloud query"
    assert result.semantic_provider == "cloud-test"


def test_follow_up_without_request_context_uses_stored_issue_for_rewrite() -> None:
    stored_issue = {"issue_summary": "Payment API is unavailable after deployment"}

    result = _service().understand("How can I prevent this?", stored_issue, {}, [])

    assert "Payment API is unavailable after deployment" in result.rewritten_query
    assert result.current_issue == stored_issue


def test_follow_up_uses_semantic_provider_with_stored_issue() -> None:
    provider = StaticProvider(SemanticUnderstanding("How can Payment API deployment failures be prevented?", {}, False, 0.95))
    stored_issue = {"issue_summary": "Payment API is unavailable after deployment"}

    result = _service(provider).understand("How can I prevent this?", stored_issue, {}, [])

    assert provider.calls == 1
    assert result.rewritten_query == "How can Payment API deployment failures be prevented?"
    assert result.semantic_provider == "local-test"


def test_greeting_does_not_use_semantic_provider() -> None:
    provider = StaticProvider(SemanticUnderstanding("Unused", {}, False, 0.95))

    _service(provider).understand("Hello", {}, {}, [])

    assert provider.calls == 0


def test_conversational_summary_requests_are_classified_as_summary_requests() -> None:
    classifier = QueryClassifier()

    assert classifier.classify("Can you summarize the whole thing?", True) == "SUMMARY_REQUEST"
    assert classifier.classify("Please recap our discussion so far.", True) == "SUMMARY_REQUEST"


def test_document_summary_request_remains_a_knowledge_query() -> None:
    classifier = QueryClassifier()

    assert classifier.classify("Summarize the Payment API documentation.", True) == "KNOWLEDGE_QUERY"