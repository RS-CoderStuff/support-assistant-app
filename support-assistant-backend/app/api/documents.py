from pathlib import PurePosixPath
from uuid import uuid4

from fastapi import APIRouter, Depends, File, UploadFile

from app.dependencies import get_jobs, get_queue, get_s3
from app.models.job import IngestionJob
from app.queue.sqs_service import SQSService
from app.storage.dynamodb_repository import DynamoDBJobRepository
from app.storage.s3_service import S3Service

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", status_code=202)
def upload_document(file: UploadFile = File(...), s3: S3Service = Depends(get_s3), jobs: DynamoDBJobRepository = Depends(get_jobs), queue: SQSService = Depends(get_queue)) -> dict:
    document_id, job_id = f"DOC-{uuid4().hex}", f"JOB-{uuid4().hex}"
    source_uri = s3.upload_raw(file.file.read(), "incoming", file.filename or "upload", document_id, file.content_type)
    jobs.save(IngestionJob(job_id=job_id, document_id=document_id, source_uri=source_uri, source_type="unknown", document_type="document", original_file_name=PurePosixPath(file.filename or "upload").name, content_type=file.content_type))
    queue.enqueue(job_id)
    return {"document_id": document_id, "job_id": job_id, "status": "QUEUED"}
