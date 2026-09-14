from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ParseContext(BaseModel):
    document_id: str
    source_uri: str
    file_name: str
    content_type: str | None = None
    source_type: str = "unknown"
    document_type: str = "document"
    metadata: dict[str, Any] = Field(default_factory=dict)


class ParsedDocument(BaseModel):
    document_id: str
    title: str
    content: str
    source_type: str
    document_type: str
    source_uri: str
    original_file_name: str
    content_type: str | None = None
    extracted_metadata: dict[str, Any] = Field(default_factory=dict)


class KnowledgeChunk(BaseModel):
    chunk_id: str = Field(default_factory=lambda: f"CHK-{uuid4().hex}")
    document_id: str
    sequence: int
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class KnowledgeDocument(BaseModel):
    document_id: str
    title: str
    content: str
    source_type: str
    document_type: str
    original_file_name: str
    source_uri: str
    content_type: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    chunks: list[KnowledgeChunk] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
