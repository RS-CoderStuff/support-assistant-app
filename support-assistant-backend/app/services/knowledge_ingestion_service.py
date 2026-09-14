from typing import Protocol

from app.models.document import KnowledgeChunk, KnowledgeDocument, ParseContext
from app.models.job import IngestionJob, JobStatus
from app.parsers.registry import ParserRegistry
from app.processors.chunker import Chunker
from app.processors.metadata import BedrockMetadataSerializer, MetadataEnricher
from app.processors.normalizer import Normalizer
from app.processors.sanitizer import Sanitizer


class SourceStorage(Protocol):
    def read_uri(self, source_uri: str) -> bytes: ...
    def upload_chunk(self, chunk: KnowledgeChunk) -> str: ...
    def upload_sidecar(self, destination_uri: str, sidecar: dict) -> None: ...


class JobStore(Protocol):
    def get(self, job_id: str) -> IngestionJob | None: ...
    def save(self, job: IngestionJob) -> None: ...


class KnowledgeIngestionService:
    def __init__(self, registry: ParserRegistry, normalizer: Normalizer, sanitizer: Sanitizer, enricher: MetadataEnricher, chunker: Chunker, storage: SourceStorage, jobs: JobStore, serializer: BedrockMetadataSerializer | None = None) -> None:
        self.registry, self.normalizer, self.sanitizer = registry, normalizer, sanitizer
        self.enricher, self.chunker, self.storage, self.jobs = enricher, chunker, storage, jobs
        self.serializer = serializer or BedrockMetadataSerializer()

    def process(self, job_id: str) -> list[KnowledgeDocument]:
        job = self.jobs.get(job_id)
        if job is None:
            raise ValueError(f"Job not found: {job_id}")
        if job.status is JobStatus.READY_FOR_KB:
            return []
        try:
            self._status(job, JobStatus.VALIDATING)
            source = self.storage.read_uri(job.source_uri)
            self._status(job, JobStatus.PARSING)
            parsed = self.registry.parse(source, ParseContext(document_id=job.document_id, source_uri=job.source_uri, file_name=job.original_file_name, content_type=job.content_type, source_type=job.source_type, document_type=job.document_type, metadata=job.metadata))
            documents = []
            for item in parsed:
                job.source_type = item.source_type
                job.document_type = item.document_type
                self._status(job, JobStatus.NORMALIZING)
                content = self.normalizer.normalize(item.content)
                self._status(job, JobStatus.SANITIZING)
                content, _ = self.sanitizer.sanitize(content)
                self._status(job, JobStatus.ENRICHING)
                metadata = self.enricher.enrich(item, job.metadata)
                self._status(job, JobStatus.CHUNKING)
                chunks = self.chunker.chunk(item.document_id, content, metadata)
                document = KnowledgeDocument(document_id=item.document_id, title=item.title, content=content, source_type=item.source_type, document_type=item.document_type, original_file_name=item.original_file_name, source_uri=item.source_uri, content_type=item.content_type, metadata=metadata, chunks=chunks)
                self._status(job, JobStatus.STORING)
                for chunk in chunks:
                    destination_uri = self.storage.upload_chunk(chunk)
                    chunk_metadata = {**metadata, "document_id": chunk.document_id, "chunk_id": chunk.chunk_id, "chunk_sequence": chunk.sequence, "source_file_name": item.original_file_name}
                    self.storage.upload_sidecar(destination_uri, self.serializer.serialize(chunk_metadata))
                job.destination_uri = destination_uri.rsplit("/chunks/", 1)[0] + "/chunks/"
                documents.append(document)
            self._status(job, JobStatus.READY_FOR_KB)
            return documents
        except Exception as error:
            job.status, job.error = JobStatus.FAILED, str(error)
            self.jobs.save(job)
            raise

    def _status(self, job: IngestionJob, status: JobStatus) -> None:
        job.status = status
        self.jobs.save(job)
