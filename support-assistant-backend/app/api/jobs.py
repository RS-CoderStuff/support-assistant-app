from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_jobs
from app.storage.dynamodb_repository import DynamoDBJobRepository

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{job_id}")
def job_status(job_id: str, jobs: DynamoDBJobRepository = Depends(get_jobs)) -> dict:
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(404, "Job not found")
    return job.model_dump(mode="json")
