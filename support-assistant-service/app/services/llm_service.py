from typing import Protocol

from app.aws.bedrock_client import BedrockRuntimeClient
from app.config.settings import Settings
from app.exceptions.exceptions import LLMInvocationException
from app.utils.logging import log_event, log_exception


class LLMService(Protocol):
    def generate(self, prompt: str) -> str: ...


class BedrockLLMService:
    def __init__(self, client: BedrockRuntimeClient, settings: Settings) -> None:
        self.client = client
        self.settings = settings

    def generate(self, prompt: str) -> str:
        if not self.settings.answer_model_id:
            log_event("llm_generation_skipped", reason="answer_model_id_not_configured")
            return "I could not find sufficient verified information in the support knowledge base to answer this question confidently."
        try:
            log_event("llm_generation_started", model_id=self.settings.answer_model_id, prompt_length=len(prompt), max_output_tokens=self.settings.llm_max_output_tokens)
            response = self.client.client.converse(modelId=self.settings.answer_model_id, messages=[{"role": "user", "content": [{"text": prompt}]}], inferenceConfig={"temperature": self.settings.llm_temperature, "maxTokens": self.settings.llm_max_output_tokens})
            answer = response["output"]["message"]["content"][0]["text"]
            log_event("llm_generation_completed", model_id=self.settings.answer_model_id, answer_length=len(answer), usage=response.get("usage", {}), latency_ms=response.get("metrics", {}).get("latencyMs"))
            return answer
        except Exception as error:
            log_exception("llm_generation_failed", model_id=self.settings.answer_model_id, error_type=type(error).__name__, error_message=str(error))
            raise LLMInvocationException() from error
