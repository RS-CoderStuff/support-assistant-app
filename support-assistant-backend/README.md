# Support Knowledge Ingestion Service

Phase 1 prepares support knowledge for an Amazon Bedrock Knowledge Base. It accepts uploads or existing S3 objects, preserves raw files, asynchronously processes them through SQS, writes normalized and sanitized text chunks plus a Bedrock metadata sidecar for every chunk to an enriched bucket, and tracks job status in DynamoDB. It does not create embeddings, vector indexes, or RAG responses.

## Architecture

`API -> raw S3 / job repository / SQS -> worker -> parser registry -> normalizer -> sanitizer -> metadata enricher -> chunker -> enriched S3 -> Bedrock sync adapter`

Supported parsers are JSON, PDF (PyMuPDF), log diagnostic windows, CSV records, text, and Markdown. The canonical `KnowledgeDocument` and `KnowledgeChunk` models allow Phase 2 retrieval to consume source and business metadata consistently.

## Local setup

1. Create and activate a Python 3.11+ virtual environment.
2. Install dependencies: `pip install -e .[dev]`.
3. Copy `.env.example` to `.env` and set AWS resource values.
4. Run the API and worker together: `python -m app.run_local`.

The local launcher starts Uvicorn at `http://localhost:8000` and the SQS worker in the same terminal. Use `Ctrl+C` to stop both processes. To run them separately, use `uvicorn app.main:app --reload` and `python -m app.workers.ingestion_worker`.

For containers, configure `.env` and run `docker compose up --build`.

## AWS prerequisites

Create separate raw and enriched S3 buckets, an SQS queue with a dead-letter queue, and a DynamoDB table named by `DYNAMODB_TABLE` with string keys `PK` and `SK`. Grant the API/worker identity S3 get/put/head/list access for these buckets, SQS send/receive/delete access, DynamoDB get/put access, and Bedrock Agent ingestion permissions. Configure the Bedrock data source to consume the enriched bucket.

## API

- `POST /api/v1/knowledge/documents`: multipart upload; queues raw content for processing.
- `POST /api/v1/knowledge/s3`: queues an existing S3 object.
- `POST /api/v1/knowledge/s3/batch`: queues asynchronous discovery for an S3 prefix.
- `GET /api/v1/knowledge/jobs/{job_id}`: returns ingestion state.
- `POST /api/v1/knowledge/sync`: starts a Bedrock Knowledge Base ingestion job.
- `GET /api/v1/knowledge/sync/{sync_job_id}?knowledge_base_id=...&data_source_id=...`: returns Bedrock ingestion status.

Example upload:

```bash
curl -F file=@sample-data/json/INC-10001.json \
  http://localhost:8000/api/v1/knowledge/documents
```

The enriched output contains application-managed chunks: `enriched/{source_type}/{document_id}/chunks/chunk-0001.txt` and `chunk-0001.txt.metadata.json`. Every sidecar has `metadataAttributes`, including document and chunk IDs, for Bedrock filtering. Configure the Bedrock data source for no chunking.

JSON files with a `ticket_id` are classified as `historical_ticket` and `support_ticket`. Other unclassified uploads use `source_type=uploaded_document` and a parser-derived `document_type`, such as `pdf`, `csv`, `log`, `txt`, or `markdown`.

## Tests

Run unit tests with `pytest tests/unit`. They require no AWS credentials and validate the processing pipeline, parsers/registry, processors, and API adapters. AWS integration tests are skipped unless `RUN_AWS_INTEGRATION_TESTS=1` is set with configured resources.

## Limitations

The worker is intentionally a simple long-poll process. Production deployment should configure SQS visibility timeout and DLQ redrive policy, emit CloudWatch metrics from the existing state transitions, and extend the batch-discovery worker into paginated continuation messages for very large prefixes. The Bedrock adapter maps the standard start/status APIs but does not persist sync history.

## Phase 2

Consume enriched S3 documents/chunks with Bedrock Knowledge Base retrieval, metadata filters, hybrid search, reranking, and access-control policies. Keep retrieval and orchestration outside this ingestion service.
