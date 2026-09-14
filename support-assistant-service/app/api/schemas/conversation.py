from typing import Any

from pydantic import BaseModel


class ConversationResponse(BaseModel):
    conversation_id: str
    user_id: str
    status: str
    summary: str
    current_issue: dict[str, Any]
    active_evidence: list[str]
    created_at: str | None = None
    updated_at: str | None = None


class ConversationMessageResponse(BaseModel):
    sequence: int
    role: str
    content: str
    created_at: str


class MessagePage(BaseModel):
    items: list[ConversationMessageResponse]
    next_cursor: str | None = None
