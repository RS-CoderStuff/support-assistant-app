from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    aws_region: str = "us-east-1"
    raw_bucket: str = ""
    enriched_bucket: str = ""
    ingestion_queue_url: str = ""
    dynamodb_table: str = "support-ai-ingestion"
    bedrock_kb_id: str = ""
    bedrock_data_source_id: str = ""
    sanitizer_mode: str = "MASK"


@lru_cache
def get_settings() -> Settings:
    return Settings()
