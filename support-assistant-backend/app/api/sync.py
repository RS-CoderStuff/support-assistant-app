from fastapi import APIRouter, Depends

from app.bedrock.knowledge_base import KnowledgeBaseAdapter
from app.config.settings import get_settings
from app.models.requests import SyncRequest

router = APIRouter(prefix="/sync", tags=["sync"])


def get_adapter() -> KnowledgeBaseAdapter:
    return KnowledgeBaseAdapter(get_settings().aws_region)


@router.post("", status_code=202)
def start_sync(request: SyncRequest, adapter: KnowledgeBaseAdapter = Depends(get_adapter)) -> dict:
    job = adapter.start_ingestion(request.knowledge_base_id, request.data_source_id)
    return {"sync_job_id": job["ingestionJobId"], "knowledge_base_id": request.knowledge_base_id, "status": job["status"]}


@router.get("/{sync_job_id}")
def get_sync(sync_job_id: str, knowledge_base_id: str, data_source_id: str, adapter: KnowledgeBaseAdapter = Depends(get_adapter)) -> dict:
    job = adapter.get_ingestion_status(knowledge_base_id, data_source_id, sync_job_id)
    statistics = job.get("statistics", {})
    return {"sync_job_id": sync_job_id, "knowledge_base_id": knowledge_base_id, "status": job["status"], "statistics": {"scanned": statistics.get("numberOfDocumentsScanned", 0), "processed": statistics.get("numberOfDocumentsSucceeded", 0), "failed": statistics.get("numberOfDocumentsFailed", 0)}}
