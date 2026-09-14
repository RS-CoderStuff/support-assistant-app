from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from app.models.document import utc_now


class JobStatus(StrEnum):
    QUEUED = "QUEUED"
    VALIDATING = "VALIDATING"
    PARSING = "PARSING"
    NORMALIZING = "NORMALIZING"
    SANITIZING = "SANITIZING"
    ENRICHING = "ENRICHING"
    CHUNKING = "CHUNKING"
    STORING = "STORING"
    READY_FOR_KB = "READY_FOR_KB"
    FAILED = "FAILED"


class IngestionJob(BaseModel):
    job_id: str
    document_id: str
    status: JobStatus = JobStatus.QUEUED
    source_uri: str
    source_type: str
    document_type: str = "document"
    original_file_name: str
    content_type: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    destination_uri: str | None = None
    error: str | None = None
    retry_count: int = 0
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
