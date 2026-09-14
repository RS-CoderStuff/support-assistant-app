from dataclasses import dataclass
from uuid import uuid4

from langgraph.graph import END, START, StateGraph

from app.graph.state import AssistantState
from app.aws.bedrock_kb_client import BedrockKnowledgeBaseClient
from app.models.conversation import Conversation
from app.services.conversation_manager import ConversationManager
from app.services.conversation_updater import ConversationUpdater
from app.services.evidence_validator import EvidenceValidator
from app.services.guardrail_service import InputGuardrail, OutputGuardrail
from app.services.llm_service import LLMService
from app.services.metadata_extractor import MetadataExtractionService
from app.services.metadata_filter_builder import MetadataFilterBuilder
from app.services.query_classifier import QueryClassifier
from app.services.query_rewriter import QueryRewriteService
from app.services.query_understanding import QueryUnderstandingService
from app.services.retrieval_decision import RetrievalDecisionService
from app.services.reranker import Reranker
from app.services.prompt_builder import PromptBuilder
from app.utils.logging import log_event


@dataclass
class AssistantWorkflow:
    classifier: QueryClassifier
    decision: RetrievalDecisionService
    rewriter: QueryRewriteService
    extractor: MetadataExtractionService
    filter_builder: MetadataFilterBuilder
    conversation_manager: ConversationManager
    retriever: BedrockKnowledgeBaseClient
    reranker: Reranker
    validator: EvidenceValidator
    prompt_builder: PromptBuilder
    llm: LLMService
    input_guardrail: InputGuardrail
    output_guardrail: OutputGuardrail
    updater: ConversationUpdater
    retrieval_top_k: int
    query_understanding: QueryUnderstandingService | None = None

    def invoke(self, state: AssistantState) -> AssistantState:
        state = {**state, "request_id": state.get("request_id", f"REQ-{uuid4().hex}")}
        log_event("assistant_workflow_started", request_id=state["request_id"], conversation_id=state["conversation_id"], user_id=state["user_id"], message_length=len(state["user_message"]))
        graph = self._build_graph()
        result = graph.invoke(state)
        log_event("assistant_workflow_completed", request_id=state["request_id"], conversation_id=state["conversation_id"], query_type=result.get("query_type"), retrieval_performed=result.get("retrieval_required"), documents_used=len(result.get("validated_evidence", [])), confidence=result.get("confidence"))
        return result

    def _build_graph(self):
        graph = StateGraph(AssistantState)
        graph.add_node("load_conversation", self._load_conversation)
        graph.add_node("input_guardrail", self._input_guardrail)
        graph.add_node("understand", self._understand)
        graph.add_node("retrieve", self._retrieve)
        graph.add_node("answer", self._answer)
        graph.add_node("update_conversation", self._update_conversation)
        graph.add_edge(START, "load_conversation")
        graph.add_edge("load_conversation", "input_guardrail")
        graph.add_edge("input_guardrail", "understand")
        graph.add_conditional_edges("understand", lambda state: "retrieve" if state["retrieval_required"] else "answer")
        graph.add_edge("retrieve", "answer")
        graph.add_edge("answer", "update_conversation")
        graph.add_edge("update_conversation", END)
        return graph.compile()

    def _load_conversation(self, state: AssistantState) -> AssistantState:
        conversation = self.conversation_manager.load_or_create(state["conversation_id"], state["user_id"])
        self.conversation_manager.persist_user_message(conversation.conversation_id, state["user_message"])
        log_event("conversation_loaded", request_id=state["request_id"], conversation_id=conversation.conversation_id, status=conversation.status, active_evidence_count=len(conversation.active_evidence))
        return {"conversation_summary": conversation.summary, "current_issue": conversation.current_issue, "active_evidence": conversation.active_evidence, "recent_messages": self.conversation_manager.recent(conversation.conversation_id), "conversation": conversation}

    def _input_guardrail(self, state: AssistantState) -> AssistantState:
        self.input_guardrail.validate(state["user_message"])
        log_event("input_guardrail_allowed", request_id=state["request_id"], conversation_id=state["conversation_id"])
        return {"guardrail_result": {"input": "allowed"}}

    def _understand(self, state: AssistantState) -> AssistantState:
        if self.query_understanding:
            return self._understand_with_service(state)
        query_type = self.classifier.classify(state["user_message"], bool(state.get("conversation_summary") or state.get("current_issue")))
        request_context = state.get("context", {})
        stored_issue = state.get("current_issue", {})
        rewrite_context = request_context or stored_issue if query_type == "FOLLOW_UP" else {}
        rewritten_query = self.rewriter.rewrite(state["user_message"], rewrite_context)
        metadata = self.extractor.extract(rewritten_query, request_context)
        if query_type == "NEW_ISSUE":
            current_issue = {"issue_summary": state["user_message"], **metadata}
        elif request_context:
            current_issue = metadata
        elif query_type == "FOLLOW_UP":
            current_issue = {**stored_issue, **metadata}
        else:
            current_issue = stored_issue
        metadata_filter = self.filter_builder.build(request_context)
        retrieval_required, retrieval_basis = self.decision.decide(query_type, state.get("active_evidence", []), state["user_message"])
        log_event("_understand.query_understood", request_id=state["request_id"], conversation_id=state["conversation_id"], original_query=state["user_message"], rewritten_query=rewritten_query, query_type=query_type, current_issue=current_issue, request_context=request_context, extracted_metadata=metadata, metadata_filter=metadata_filter, filter_source="request_context" if request_context else "none", rewrite_context_source="request_context" if request_context and query_type == "FOLLOW_UP" else "stored_issue" if rewrite_context else "none", active_evidence_count=len(state.get("active_evidence", [])), retrieval_required=retrieval_required, retrieval_basis=retrieval_basis)
        return {
            "request_id": state.get("request_id", f"REQ-{uuid4().hex}"),
            "query_type": query_type,
            "current_issue": current_issue,
            "rewritten_query": rewritten_query,
            "extracted_metadata": metadata,
            "metadata_filter": metadata_filter,
            "retrieval_required": retrieval_required,
        }

    def _understand_with_service(self, state: AssistantState) -> AssistantState:
        request_context = state.get("context", {})
        result = self.query_understanding.understand(state["user_message"], state.get("current_issue", {}), request_context, state.get("active_evidence", []), request_id=state["request_id"], conversation_id=state["conversation_id"])
        metadata_filter = self.filter_builder.build(request_context)
        log_event("_understand_with_service.query_understood", request_id=state["request_id"], conversation_id=state["conversation_id"], original_query=state["user_message"], rewritten_query=result.rewritten_query, query_type=result.query_type, current_issue=result.current_issue, request_context=request_context, extracted_metadata=result.extracted_metadata, metadata_filter=metadata_filter, filter_source="request_context" if request_context else "none", semantic_provider=result.semantic_provider, active_evidence_count=len(state.get("active_evidence", [])), retrieval_required=result.retrieval_required, retrieval_basis=result.retrieval_basis)
        return {"request_id": state["request_id"], "query_type": result.query_type, "current_issue": result.current_issue, "rewritten_query": result.rewritten_query, "extracted_metadata": result.extracted_metadata, "metadata_filter": metadata_filter, "retrieval_required": result.retrieval_required}

    def _retrieve(self, state: AssistantState) -> AssistantState:
        log_event("retrieval_pipeline_started", request_id=state["request_id"], conversation_id=state["conversation_id"], rewritten_query=state["rewritten_query"], metadata_filter=state["metadata_filter"], top_k=self.retrieval_top_k)
        retrieved = self.retriever.retrieve(state["rewritten_query"], state["metadata_filter"], self.retrieval_top_k, request_id=state["request_id"], conversation_id=state["conversation_id"])
        log_event("knowledge_base_results_received", request_id=state["request_id"], conversation_id=state["conversation_id"], documents_retrieved=len(retrieved))
        reranked = self.reranker.rank(state["rewritten_query"], retrieved)
        log_event("knowledge_base_results_reranked", request_id=state["request_id"], conversation_id=state["conversation_id"], documents_reranked=len(reranked))
        validated = self.validator.validate(reranked, state.get("context", {})).documents
        log_event("knowledge_base_results_validated", request_id=state["request_id"], conversation_id=state["conversation_id"], documents_validated=len(validated))
        citations = [{"source_id": item.source_id, "source_type": item.source_type, "title": item.title, "relevance_score": item.score} for item in validated]
        log_event("evidence_processed", request_id=state["request_id"], conversation_id=state["conversation_id"], documents_retrieved=len(retrieved), documents_reranked=len(reranked), documents_validated=len(validated))
        return {"retrieved_documents": retrieved, "reranked_documents": reranked, "validated_evidence": validated, "citations": citations}

    def _answer(self, state: AssistantState) -> AssistantState:
        if state["query_type"] == "GREETING":
            answer = "Hello. How can I help with a support issue?"
        elif state["retrieval_required"] and not state.get("validated_evidence"):
            answer = "I could not find sufficient verified information in the support knowledge base to answer this question confidently."
        else:
            prompt = self.prompt_builder.build(state.get("conversation_summary", ""), state.get("current_issue", {}), state.get("recent_messages", []), state.get("validated_evidence", []), state["user_message"])
            answer = self.output_guardrail.validate(self.llm.generate(prompt))
        confidence = min(0.99, sum(item.score for item in state.get("validated_evidence", [])) / max(1, len(state.get("validated_evidence", []))))
        log_event("answer_created", request_id=state["request_id"], conversation_id=state["conversation_id"], query_type=state["query_type"], answer_length=len(answer), confidence=confidence, citation_count=len(state.get("citations", [])))
        return {"answer": answer, "confidence": confidence, "citations": state.get("citations", [])}

    def _update_conversation(self, state: AssistantState) -> AssistantState:
        self.updater.update(state["conversation"], state["answer"], state.get("current_issue", {}), state.get("citations", []))
        log_event("conversation_updated", request_id=state["request_id"], conversation_id=state["conversation_id"], citation_count=len(state.get("citations", [])))
        return {}


