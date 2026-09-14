from fastapi.testclient import TestClient

from app.api.sync import get_adapter
from app.dependencies import get_jobs, get_queue, get_s3
from app.main import app
from app.models.job import IngestionJob


class FakeS3:
    def __init__(self): self.data = {}
    def upload_raw(self, source, source_type, file_name, document_id, content_type):
        uri = f"s3://raw/raw/{source_type}/{document_id}/{file_name}"
        self.data[uri] = source
        return uri
    def get_object_metadata(self, bucket, key):
        return {"ContentType": "application/json"} if key == "json/ticket.json" else None
    def uri(self, bucket, key): return f"s3://{bucket}/{key}"
    def list_keys(self, bucket, prefix): return ["json/ticket.json"]


class FakeJobs:
    def __init__(self): self.items = {}
    def save(self, job): self.items[job.job_id] = job
    def get(self, job_id): return self.items.get(job_id)


class FakeQueue:
    def __init__(self): self.messages = []
    def enqueue(self, job_id): self.messages.append({"job_id": job_id})
    def enqueue_payload(self, payload): self.messages.append(payload)


class FakeBedrock:
    def start_ingestion(self, kb, source): return {"ingestionJobId": "sync-1", "status": "STARTING"}
    def get_ingestion_status(self, kb, source, job): return {"status": "COMPLETE", "statistics": {"numberOfDocumentsScanned": 1, "numberOfDocumentsSucceeded": 1, "numberOfDocumentsFailed": 0}}


def client_with_fakes():
    s3, jobs, queue = FakeS3(), FakeJobs(), FakeQueue()
    app.dependency_overrides = {get_s3: lambda: s3, get_jobs: lambda: jobs, get_queue: lambda: queue, get_adapter: lambda: FakeBedrock()}
    return TestClient(app), jobs, queue


def test_upload_and_get_job():
    client, jobs, queue = client_with_fakes()
    response = client.post("/api/v1/knowledge/documents", files={"file": ("ticket.json", b'{"title":"Test"}', "application/json")})
    assert response.status_code == 202
    job_id = response.json()["job_id"]
    assert queue.messages == [{"job_id": job_id}]
    assert jobs.get(job_id).source_type == "unknown"
    assert client.get(f"/api/v1/knowledge/jobs/{job_id}").json()["status"] == "QUEUED"


def test_s3_and_batch_requests_are_queued():
    client, jobs, queue = client_with_fakes()
    response = client.post("/api/v1/knowledge/s3", json={"bucket": "raw", "key": "json/ticket.json", "source_type": "historical_ticket"})
    assert response.status_code == 202
    assert jobs.get(response.json()["job_id"]).content_type == "application/json"
    response = client.post("/api/v1/knowledge/s3/batch", json={"bucket": "raw", "prefix": "json/", "source_type": "historical_ticket"})
    assert response.status_code == 202
    assert queue.messages[-1]["batch_id"].startswith("BATCH-")


def test_sync_adapter_endpoints():
    client, _, _ = client_with_fakes()
    response = client.post("/api/v1/knowledge/sync", json={"knowledge_base_id": "kb", "data_source_id": "source"})
    assert response.json()["sync_job_id"] == "sync-1"
    assert client.get("/api/v1/knowledge/sync/sync-1?knowledge_base_id=kb&data_source_id=source").json()["status"] == "COMPLETE"
