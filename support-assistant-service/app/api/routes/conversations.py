from fastapi import APIRouter, Depends, Query

from app.api.schemas.conversation import ConversationResponse, MessagePage
from app.exceptions.exceptions import ConversationNotFoundException
from app.repositories.conversation_repository import ConversationRepository

router = APIRouter(prefix="/api/v1/conversations", tags=["conversations"])


def get_repository() -> ConversationRepository:
    from app.main import get_repository as factory
    return factory()


@router.get("/{conversation_id}", response_model=ConversationResponse)
def get_conversation(conversation_id: str, repository: ConversationRepository = Depends(get_repository)) -> ConversationResponse:
    conversation = repository.get(conversation_id)
    if not conversation:
        raise ConversationNotFoundException()
    return ConversationResponse(conversation_id=conversation.conversation_id, user_id=conversation.user_id, status=conversation.status, summary=conversation.summary, current_issue=conversation.current_issue, active_evidence=[item["source_id"] for item in conversation.active_evidence], created_at=conversation.created_at, updated_at=conversation.updated_at)


@router.get("/{conversation_id}/messages", response_model=MessagePage)
def get_messages(conversation_id: str, limit: int = Query(default=20, ge=1, le=100), cursor: str | None = None, repository: ConversationRepository = Depends(get_repository)) -> MessagePage:
    if not repository.get(conversation_id):
        raise ConversationNotFoundException()
    items, next_cursor = repository.messages(conversation_id, limit, cursor)
    return MessagePage(items=items, next_cursor=next_cursor)


@router.post("/{conversation_id}/close", status_code=204)
def close_conversation(conversation_id: str, repository: ConversationRepository = Depends(get_repository)) -> None:
    repository.close(conversation_id)


@router.delete("/{conversation_id}", status_code=204)
def delete_conversation(conversation_id: str, repository: ConversationRepository = Depends(get_repository)) -> None:
    repository.close(conversation_id)