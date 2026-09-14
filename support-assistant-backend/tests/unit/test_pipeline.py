from app.models.document import ParseContext
from app.models.job import IngestionJob, JobStatus
from app.parsers.csv_parser import CSVParser
from app.parsers.json_parser import JSONParser
from app.parsers.log_parser import LogParser
from app.parsers.markdown_parser import MarkdownParser
from app.parsers.pdf_parser import PDFParser
from app.parsers.registry import ParserRegistry
from app.parsers.text_parser import TextParser
from app.processors.chunker import Chunker
from app.processors.metadata import MetadataEnricher
from app.processors.normalizer import Normalizer
from app.processors.sanitizer import Sanitizer
from app.services.knowledge_ingestion_service import KnowledgeIngestionService


class MemoryStore:
    def __init__(self, job: IngestionJob) -> None:
        self.job = job
        self.objects: dict[str, bytes] = {job.source_uri: b'{"ticket_id":"INC-10001","title":"Payment failure","description":"API returns 503 password=secret","resolution":"Restarted service","product":"payments"}'}
        self.sidecars: dict[str, dict] = {}

    def get(self, job_id: str): return self.job if job_id == self.job.job_id else None
    def save(self, job: IngestionJob): self.job = job
    def read_uri(self, uri: str) -> bytes: return self.objects[uri]
    def upload_chunk(self, chunk) -> str:
        uri = f"s3://enriched/{chunk.document_id}/chunks/chunk-{chunk.sequence:04d}.txt"
        self.objects[uri] = chunk.content.encode()
        return uri
    def upload_sidecar(self, destination_uri: str, sidecar: dict) -> None: self.sidecars[destination_uri] = sidecar


def test_json_job_is_processed_and_sanitized():
    job = IngestionJob(job_id="JOB-1", document_id="DOC-1", source_uri="s3://raw/ticket.json", source_type="unknown", document_type="document", original_file_name="ticket.json", content_type="application/json")
    store = MemoryStore(job)
    service = KnowledgeIngestionService(ParserRegistry([JSONParser()]), Normalizer(), Sanitizer(), MetadataEnricher(), Chunker(80, 10), store, store)
    documents = service.process("JOB-1")
    assert store.job.status is JobStatus.READY_FOR_KB
    assert store.job.source_type == "historical_ticket"
    assert store.job.document_type == "support_ticket"
    assert "secret" not in documents[0].content
    assert all(sidecar["metadataAttributes"]["product"] == "payments" for sidecar in store.sidecars.values())
    assert all("chunk_id" in sidecar["metadataAttributes"] for sidecar in store.sidecars.values())
    assert all(sidecar["metadataAttributes"]["source_file_name"] == "ticket.json" for sidecar in store.sidecars.values())
    assert job.destination_uri.endswith("/chunks/")
    assert all("chunks" in uri for uri in store.objects if uri != job.source_uri)
    assert documents[0].chunks


def test_registry_supports_all_required_types():
    registry = ParserRegistry([JSONParser(), PDFParser(), LogParser(), CSVParser(), MarkdownParser(), TextParser()])
    assert registry.parsers[0].supports("ticket.json", None)
    assert registry.parsers[1].supports("manual.pdf", None)
    assert registry.parsers[2].supports("service.log", None)
    assert registry.parsers[3].supports("tickets.csv", None)
    assert registry.parsers[4].supports("guide.md", None)
    assert registry.parsers[5].supports("notes.txt", None)


def test_json_ticket_derives_document_classification_and_metadata():
    document = JSONParser().parse(b'{"ticket_id":"INC-1","title":"Failure","product":"payments","team":"platform"}', ParseContext(document_id="DOC-1", source_uri="s3://raw/ticket.json", file_name="ticket.json", source_type="unknown"))[0]
    assert document.source_type == "historical_ticket"
    assert document.document_type == "support_ticket"
    assert document.extracted_metadata["product"] == "payments"
    assert document.extracted_metadata["team"] == "platform"


def test_text_document_uses_file_type_fallback_classification():
    document = TextParser().parse(b"Runbook content", ParseContext(document_id="DOC-1", source_uri="s3://raw/runbook.txt", file_name="runbook.txt", source_type="unknown"))[0]
    assert document.source_type == "uploaded_document"
    assert document.document_type == "txt"
