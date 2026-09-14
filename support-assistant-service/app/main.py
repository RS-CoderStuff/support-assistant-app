from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.routes import assistant, conversations, health
from app.aws.bedrock_client import BedrockRuntimeClient
from app.aws.bedrock_kb_client import BedrockKnowledgeBaseClient
from app.config.settings import get_settings
from app.exceptions.exceptions import ApplicationException
from app.graph.assistant_graph import AssistantWorkflow
from app.repositories.conversation_repository import DynamoDBConversationRepository, InMemoryConversationRepository
from app.services.conversation_manager import ConversationManager
from app.services.conversation_updater import ConversationUpdater
from app.services.evidence_validator import EvidenceValidator
from app.services.guardrail_service import InputGuardrail, OutputGuardrail
from app.services.llm_service import BedrockLLMService
from app.services.metadata_extractor import MetadataExtractionService
from app.services.metadata_filter_builder import MetadataFilterBuilder
from app.services.prompt_builder import PromptBuilder
from app.services.query_classifier import QueryClassifier
from app.services.query_rewriter import QueryRewriteService
from app.services.query_understanding import BedrockSemanticUnderstandingProvider, OllamaSemanticUnderstandingProvider, QueryUnderstandingService
from app.services.retrieval_decision import RetrievalDecisionService
from app.services.reranker import Reranker
from app.utils.logging import configure_logging, log_event, log_exception

settings = get_settings()
configure_logging()
app = FastAPI(title=settings.application_name, version="0.1.0")
app.include_router(assistant.router)
app.include_router(conversations.router)
app.include_router(health.router)


@app.exception_handler(ApplicationException)
async def handle_application_exception(_: Request, error: ApplicationException) -> JSONResponse:
	log_event("application_error_returned", error_type=type(error).__name__, status_code=error.status_code)
	return JSONResponse(status_code=error.status_code, content={"detail": error.public_message})


@app.middleware("http")
async def request_logging(request: Request, call_next):
	try:
		response = await call_next(request)
		log_event("request_completed", method=request.method, path=request.url.path, status_code=response.status_code)
		return response
	except Exception as error:
		log_exception("request_failed", method=request.method, path=request.url.path, error_type=type(error).__name__, error_message=str(error))
		raise


def get_repository():
	if settings.environment == "dev" and not settings.conversation_table_name:
		if not hasattr(app.state, "development_repository"):
			app.state.development_repository = InMemoryConversationRepository()
		return app.state.development_repository
	from app.aws.dynamodb_client import DynamoDBClient
	return DynamoDBConversationRepository(DynamoDBClient(settings).table)


def get_workflow() -> AssistantWorkflow:
	repository = get_repository()
	classifier = QueryClassifier()
	decision = RetrievalDecisionService()
	rewriter = QueryRewriteService()
	extractor = MetadataExtractionService()
	filter_builder = MetadataFilterBuilder()
	runtime_client = BedrockRuntimeClient(settings)
	local_provider = OllamaSemanticUnderstandingProvider(settings.query_understanding_ollama_url, settings.query_understanding_local_model, settings.query_understanding_timeout_seconds) if settings.query_understanding_local_model else None
	cloud_model_id = settings.query_understanding_cloud_model_id or settings.answer_model_id
	cloud_provider = BedrockSemanticUnderstandingProvider(runtime_client, cloud_model_id, settings.query_understanding_timeout_seconds) if settings.query_understanding_cloud_fallback_enabled and cloud_model_id else None
	query_understanding = QueryUnderstandingService(classifier, rewriter, extractor, decision, local_provider, cloud_provider, settings.query_understanding_minimum_confidence)
	return AssistantWorkflow(
		classifier=classifier, decision=decision, rewriter=rewriter,
		extractor=extractor, filter_builder=filter_builder,
		conversation_manager=ConversationManager(repository, settings.conversation_recent_messages),
		retriever=BedrockKnowledgeBaseClient(settings), reranker=Reranker(settings.reranking_enabled, settings.reranking_top_k),
		validator=EvidenceValidator(settings.evidence_minimum_score, settings.evidence_minimum_sources, settings.evidence_final_top_k),
		prompt_builder=PromptBuilder(), llm=BedrockLLMService(runtime_client, settings),
		input_guardrail=InputGuardrail(), output_guardrail=OutputGuardrail(), updater=ConversationUpdater(repository),
		retrieval_top_k=settings.retrieval_top_k, query_understanding=query_understanding,
	)
