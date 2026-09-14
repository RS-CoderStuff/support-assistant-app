import json
import logging
from pathlib import PurePosixPath
from uuid import uuid4

from app.dependencies import get_ingestion_service, get_jobs, get_queue, get_s3
from app.models.job import IngestionJob

logging.basicConfig(format="%(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


def run_once() -> int:
    queue, service = get_queue(), get_ingestion_service()
    jobs, s3 = get_jobs(), get_s3()
    processed = 0
    for message in queue.receive():
        payload = json.loads(message["Body"])
        try:
            if "batch_id" in payload:
                for key in s3.list_keys(payload["bucket"], payload["prefix"]):
                    document_id, job_id = f"DOC-{uuid4().hex}", f"JOB-{uuid4().hex}"
                    object_metadata = s3.get_object_metadata(payload["bucket"], key)
                    if object_metadata is None:
                        continue
                    jobs.save(IngestionJob(job_id=job_id, document_id=document_id, source_uri=s3.uri(payload["bucket"], key), source_type=payload["source_type"], document_type=payload["document_type"], original_file_name=PurePosixPath(key).name, content_type=object_metadata.get("ContentType"), metadata=payload.get("metadata", {})))
                    queue.enqueue(job_id)
            else:
                job_id = payload["job_id"]
                service.process(job_id)
            queue.delete(message["ReceiptHandle"])
            processed += 1
        except Exception:
            logger.exception("ingestion_failed", extra={"job_id": payload.get("job_id"), "batch_id": payload.get("batch_id")})
            raise
    return processed


if __name__ == "__main__":
    while True:
        run_once()
