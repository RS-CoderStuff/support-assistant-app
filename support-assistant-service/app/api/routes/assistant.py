from fastapi import APIRouter, Depends

from app.api.schemas.assistant import AssistantMetadata, ChatRequest, ChatResponse
from app.graph.assistant_graph import AssistantWorkflow

router = APIRouter(prefix="/api/v1/assistant", tags=["assistant"])


def get_workflow() -> AssistantWorkflow:
    from app.main import get_workflow as factory
    return factory()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, workflow: AssistantWorkflow = Depends(get_workflow)) -> ChatResponse:
    state = workflow.invoke({
        "conversation_id": request.conversation_id,
        "user_id": request.user.user_id,
        "user_message": request.message,
        "context": request.context.model_dump(exclude_none=True) if request.context else {},
    })
    return ChatResponse(
        conversation_id=request.conversation_id,
        request_id=state["request_id"],
        answer=state["answer"],
        confidence=state["confidence"],
        citations=state["citations"],
        metadata=AssistantMetadata(
            query_type=state["query_type"],
            retrieval_performed=state["retrieval_required"],
            documents_retrieved=len(state.get("retrieved_documents", [])),
            documents_reranked=len(state.get("reranked_documents", [])),
            documents_used=len(state.get("validated_evidence", [])),
        ),
    )
