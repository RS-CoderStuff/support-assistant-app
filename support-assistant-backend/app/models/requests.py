from typing import Any

from pydantic import BaseModel, Field


class S3IngestionRequest(BaseModel):
    bucket: str
    key: str
    source_type: str
    document_type: str = "document"
    metadata: dict[str, Any] = Field(default_factory=dict)


class BatchS3IngestionRequest(BaseModel):
    bucket: str
    prefix: str
    source_type: str
    document_type: str = "document"
    metadata: dict[str, Any] = Field(default_factory=dict)


class SyncRequest(BaseModel):
    knowledge_base_id: str
    data_source_id: str
