# Support Assistant Service

FastAPI and LangGraph orchestration service for customer-support resolution. It uses exactly one configured Amazon Bedrock Knowledge Base for organizational knowledge and DynamoDB only for per-conversation state.

## Run locally

```bash
python -m pip install -e '.[dev]'
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Development mode uses an explicitly local, in-memory conversation adapter and returns a controlled insufficient-evidence response when no Knowledge Base ID is configured. Set `SUPPORT_ASSISTANT_ENVIRONMENT` to a non-`dev` value plus all AWS configuration before deployment. AWS credentials are obtained from the SDK credential chain/IAM role; never add them to `.env`.

## Public API

- `POST /api/v1/assistant/chat`
- `GET /api/v1/conversations/{conversation_id}`
- `GET /api/v1/conversations/{conversation_id}/messages?limit=20&cursor=`
- `POST /api/v1/conversations/{conversation_id}/close` closes rather than destroys an auditable conversation and is the recommended endpoint.
- `DELETE /api/v1/conversations/{conversation_id}` currently has the same safe close behavior.
- `GET /health`, `GET /ready`, `/docs`, `/redoc`, `/openapi.json`

## DynamoDB design

The table uses `PK=CONVERSATION#<id>` with `SK=METADATA` for summary/state and `SK=MESSAGE#<timestamp>` for messages. Retrieved contents are not persisted; `active_evidence` stores only citation references.

## Confidence

Confidence is the mean validated reranker score, capped at `0.99`. Validation removes duplicates, inactive sources, incompatible metadata, low-score sources, and prompt-injection-like retrieved text. Insufficient evidence produces a controlled response instead of a generated technical claim.

## AWS notes

`BedrockKnowledgeBaseClient` calls lower-level `Retrieve`, never `RetrieveAndGenerate`; final generation calls `Converse`. Configure a rerank model ARN to replace the score-preserving fallback in `Reranker`. Bedrock Guardrails model and API compatibility vary by selected model and region; configure IDs/version before enabling them.

Authentication is an abstraction point. Development mode accepts an optional `X-User-Id` header; production should replace it with API Gateway/JWT identity validation before public exposure.