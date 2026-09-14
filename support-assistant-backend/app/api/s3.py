from pathlib import PurePosixPath
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_jobs, get_queue, get_s3
from app.models.job import IngestionJob
from app.models.requests import BatchS3IngestionRequest, S3IngestionRequest
from app.queue.sqs_service import SQSService
from app.storage.dynamodb_repository import DynamoDBJobRepository
from app.storage.s3_service import S3Service

router = APIRouter(prefix="/s3", tags=["s3"])


def enqueue(request: S3IngestionRequest, s3: S3Service, jobs: DynamoDBJobRepository, queue: SQSService) -> dict:
    object_metadata = s3.get_object_metadata(request.bucket, request.key)
    if object_metadata is None:
        raise HTTPException(404, "S3 object does not exist")
    document_id, job_id = f"DOC-{uuid4().hex}", f"JOB-{uuid4().hex}"
    jobs.save(IngestionJob(job_id=job_id, document_id=document_id, source_uri=s3.uri(request.bucket, request.key), source_type=request.source_type, document_type=request.document_type, original_file_name=PurePosixPath(request.key).name, content_type=object_metadata.get("ContentType"), metadata=request.metadata))
    queue.enqueue(job_id)
    return {"document_id": document_id, "job_id": job_id, "status": "QUEUED"}


@router.post("", status_code=202)
def ingest_s3(request: S3IngestionRequest, s3: S3Service = Depends(get_s3), jobs: DynamoDBJobRepository = Depends(get_jobs), queue: SQSService = Depends(get_queue)) -> dict:
    return enqueue(request, s3, jobs, queue)


@router.post("/batch", status_code=202)
def ingest_batch(request: BatchS3IngestionRequest, s3: S3Service = Depends(get_s3), jobs: DynamoDBJobRepository = Depends(get_jobs), queue: SQSService = Depends(get_queue)) -> dict:
    batch_id = f"BATCH-{uuid4().hex}"
    queue.enqueue_payload({"batch_id": batch_id, "bucket": request.bucket, "prefix": request.prefix, "source_type": request.source_type, "document_type": request.document_type, "metadata": request.metadata})
    return {"batch_id": batch_id, "status": "QUEUED"}
