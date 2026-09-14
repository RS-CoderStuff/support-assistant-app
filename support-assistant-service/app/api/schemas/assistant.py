from typing import Literal

from pydantic import BaseModel, Field


class UserContext(BaseModel):
    user_id: str = Field(min_length=1, max_length=128)
    name: str | None = Field(default=None, max_length=256)


class IssueContext(BaseModel):
    product: str | None = Field(default=None, max_length=128)
    component: str | None = Field(default=None, max_length=128)
    environment: str | None = Field(default=None, max_length=64)


class ChatRequest(BaseModel):
    conversation_id: str = Field(min_length=1, max_length=128)
    user: UserContext
    message: str = Field(min_length=1, max_length=8000)
    context: IssueContext | None = None


class Citation(BaseModel):
    source_id: str
    source_type: str
    title: str | None = None
    relevance_score: float = Field(ge=0, le=1)


class AssistantMetadata(BaseModel):
    query_type: Literal[
        "NEW_ISSUE", "FOLLOW_UP", "CLARIFICATION", "KNOWLEDGE_QUERY", "GREETING", "OUT_OF_SCOPE", "SUMMARY_REQUEST"
    ]
    retrieval_performed: bool
    documents_retrieved: int = 0
    documents_reranked: int = 0
    documents_used: int = 0


class ChatResponse(BaseModel):
    conversation_id: str
    request_id: str
    answer: str
    confidence: float = Field(ge=0, le=1)
    citations: list[Citation] = []
    metadata: AssistantMetadata
