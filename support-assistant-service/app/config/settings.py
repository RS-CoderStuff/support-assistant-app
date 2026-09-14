from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="SUPPORT_ASSISTANT_", extra="ignore")

    application_name: str = "support-assistant-service"
    environment: str = "dev"
    aws_region: str = "us-east-1"
    conversation_table_name: str | None = None
    knowledge_base_id: str | None = None
    knowledge_base_retrieval_mode: Literal["managed", "vector"] = "managed"
    rerank_model_arn: str | None = None
    answer_model_id: str | None = None
    classifier_model_id: str | None = None
    rewrite_model_id: str | None = None
    metadata_model_id: str | None = None
    query_understanding_local_model: str | None = None
    query_understanding_ollama_url: str = "http://localhost:11434"
    query_understanding_cloud_fallback_enabled: bool = False
    query_understanding_cloud_model_id: str | None = None
    query_understanding_minimum_confidence: float = Field(default=0.8, ge=0, le=1)
    query_understanding_timeout_seconds: float = Field(default=60, gt=0, le=120)
    retrieval_top_k: int = Field(default=25, ge=1, le=100)
    retrieval_max_retries: int = Field(default=1, ge=0, le=3)
    reranking_enabled: bool = True
    reranking_top_k: int = Field(default=8, ge=1, le=25)
    evidence_minimum_score: float = Field(default=0.72, ge=0, le=1)
    evidence_minimum_sources: int = Field(default=1, ge=1)
    evidence_final_top_k: int = Field(default=5, ge=1, le=8)
    conversation_recent_messages: int = Field(default=4, ge=1, le=10)
    llm_temperature: float = Field(default=0.1, ge=0, le=1)
    llm_max_output_tokens: int = Field(default=800, ge=1, le=4096)
    guardrails_enabled: bool = False
    guardrail_id: str | None = None
    guardrail_version: str | None = None
    prompt_cache_enabled: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
